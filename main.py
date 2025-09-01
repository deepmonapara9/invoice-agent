import google.generativeai as genai
import google.generativeai.types as types
import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN
import requests
from dotenv import load_dotenv
import stripe

# Load environment variables
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
stripe.api_key = os.getenv("STRIPE_API_KEY")

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"


# Gemini Model Setup
def create_customer(email: str, name: str = "", description: str = ""):
    """Create a new customer in Stripe."""
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name or email.split("@")[0],
            description=description or f"Customer created via AI agent",
        )
        return f"Customer {customer.id} created successfully for {email}"
    except Exception as e:
        return f"Error creating customer: {str(e)}"


def create_invoice(
    customer_id: str, amount: int, currency: str = "inr", description: str = ""
):
    """Create a new invoice for a customer."""
    try:
        # Convert amount to integer if it's a float
        amount = int(float(amount))

        # First check if customer exists, if not create a demo customer
        try:
            stripe.Customer.retrieve(customer_id)
        except stripe.error.InvalidRequestError:
            # Customer doesn't exist, create a demo customer with this ID format
            demo_email = f"{customer_id}@demo.com"
            demo_customer = stripe.Customer.create(
                email=demo_email,
                name=f"Demo Customer {customer_id}",
                description="Demo customer created by AI agent",
            )
            customer_id = demo_customer.id

        # Create the invoice first
        invoice = stripe.Invoice.create(
            customer=customer_id,
            currency=currency.lower(),
            description=description or "Invoice created by AI agent",
            collection_method="send_invoice",
            days_until_due=30,
        )

        # Then create an invoice item (line item) and associate it with the invoice
        invoice_item = stripe.InvoiceItem.create(
            customer=customer_id,
            invoice=invoice.id,  # Associate with the specific invoice
            amount=amount,  # Amount should already be in cents
            currency=currency.lower(),
            description=description or "Invoice item",
        )

        # Finalize the invoice to make it ready for payment
        finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)

        return f"Invoice {finalized_invoice.id} created successfully for customer {customer_id} with amount ₹{amount/100:.2f} {currency.upper()}. Total: ₹{finalized_invoice.total/100:.2f} {currency.upper()}"
    except Exception as e:
        return f"Error creating invoice: {str(e)}"


def list_invoices(customer_id: str | None = None):
    """List invoices, optionally for a specific customer."""
    try:
        if customer_id:
            invoices = stripe.Invoice.list(customer=customer_id)
        else:
            invoices = stripe.Invoice.list()
        return f"Found {len(invoices.data)} invoices."
    except Exception as e:
        return f"Error listing invoices: {str(e)}"


# Define tools for Gemini
tools = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="create_customer",
                description="Create a new customer in Stripe",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "email": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "description": genai.protos.Schema(
                            type=genai.protos.Type.STRING
                        ),
                    },
                    required=["email"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="create_invoice",
                description="Create a new invoice for a customer",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "customer_id": genai.protos.Schema(
                            type=genai.protos.Type.STRING
                        ),
                        "amount": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                        "currency": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "description": genai.protos.Schema(
                            type=genai.protos.Type.STRING
                        ),
                    },
                    required=["customer_id", "amount"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="list_invoices",
                description="List invoices, optionally for a specific customer",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "customer_id": genai.protos.Schema(
                            type=genai.protos.Type.STRING
                        ),
                    },
                    required=[],
                ),
            ),
        ]
    )
]

model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.7,
        top_p=0.8,
        max_output_tokens=2048,
    ),
    tools=tools,
    system_instruction="""
    You are a finance assistant responsible for generating and managing the invoicing process for a company. Your job is to enable the user to communicate with you using natural language to instruct you to perform tasks related to invoicing. You have the ability to create invoices, update invoices, manage customer accounts, send follow-ups and more. Your invoicing capabilities are provided using Stripe's API.

    Using the information in the conversation history, you need to execute the actions instructed to you by the user. If you do not have enough information to complete the task or you run into any issues, you should ask the user for clarification or additional information.

    Communicate with the end user in a polite and friendly tone. Your message responses should be clear and concise. Do not provide any unnecessary information or jargon.
    """,
)

# Conversation history
conversation_history = []


def run_quotation_agent(message: str):
    """Run the invoicing agent using Gemini."""
    global conversation_history

    try:
        # Send message to model
        response = model.generate_content(message)

        print(f"Response received: {response}")

        # Handle function calls if any
        if response.candidates:
            candidate = response.candidates[0]
            print(f"Candidate content: {candidate}")

            if hasattr(candidate, "content") and candidate.content:
                content = candidate.content
                print(f"Content parts: {content.parts}")

                if content.parts:
                    for part in content.parts:
                        print(f"Part: {part}")

                        if hasattr(part, "function_call") and part.function_call:
                            function_call = part.function_call
                            print(f"Function call detected: {function_call.name}")
                            print(f"Function args: {function_call.args}")

                            if function_call.name == "create_customer":
                                # Convert args to dict properly
                                args = {}
                                for key, value in function_call.args.items():
                                    args[key] = value
                                print(f"Processed args: {args}")

                                result = create_customer(**args)
                                return f"👤 {result}"

                            elif function_call.name == "create_invoice":
                                # Convert args to dict properly
                                args = {}
                                for key, value in function_call.args.items():
                                    args[key] = value
                                print(f"Processed args: {args}")

                                result = create_invoice(**args)
                                return f"✅ {result}"

                            elif function_call.name == "list_invoices":
                                args = {}
                                for key, value in function_call.args.items():
                                    args[key] = value

                                result = list_invoices(**args)
                                return f"📋 {result}"

        # If no function calls, return the regular response
        return response.text

    except Exception as e:
        print(f"Error in run_quotation_agent: {e}")
        import traceback

        traceback.print_exc()
        return (
            f"I'm sorry, I encountered an error while processing your request: {str(e)}"
        )


# FastAPI Setup
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key")
    return api_key


@app.get("/")
def read_root(api_key: str = Depends(verify_api_key)):
    return {"message": "API is working"}


@app.post("/clear-chat")
def clear_chat(api_key: str = Depends(verify_api_key)):
    """Clear the conversation history"""
    global conversation_history
    conversation_history.clear()
    return {"message": "Chat history cleared successfully", "success": True}


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await self.send_message(message, connection)


manager = ConnectionManager()


class ChatMessage(BaseModel):
    session_id: str
    message: str
    user_id: str = "user"
    timestamp: str | None = None
    message_type: str = "chat"


class ChatResponse(BaseModel):
    session_id: str
    message: str
    sender: str = "agent"
    timestamp: str
    message_type: str = "response"
    success: bool = True
    error: str | None = None


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session_id = str(uuid.uuid4())
    print(f"New WebSocket connection established with session ID: {session_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                # Parse incoming JSON message
                message_data = json.loads(data)
                chat_message = ChatMessage(**message_data)

                # Check if this is a clear command
                if (
                    chat_message.message_type == "clear"
                    or chat_message.message.lower().strip() == "/clear"
                ):
                    global conversation_history
                    conversation_history.clear()
                    response = ChatResponse(
                        session_id=chat_message.session_id,
                        message="Chat history has been cleared.",
                        timestamp=datetime.now().isoformat(),
                    )
                else:
                    # Process the message with the agent
                    agent_response = process_chat_message(chat_message.message)

                    # Create response
                    response = ChatResponse(
                        session_id=chat_message.session_id,
                        message=agent_response,
                        timestamp=datetime.now().isoformat(),
                    )

                # Send response back to client
                await manager.send_message(response.model_dump_json(), websocket)

            except json.JSONDecodeError:
                # Handle plain text messages for backward compatibility
                agent_response = process_chat_message(data)
                response = ChatResponse(
                    session_id=session_id,
                    message=agent_response,
                    timestamp=datetime.now().isoformat(),
                )
                await manager.send_message(response.model_dump_json(), websocket)

            except Exception as e:
                # Handle errors
                error_response = ChatResponse(
                    session_id=session_id,
                    message="Sorry, I encountered an error processing your message.",
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=str(e),
                )
                await manager.send_message(error_response.model_dump_json(), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"WebSocket connection closed for session: {session_id}")


def process_chat_message(message: str) -> str:
    """Process chat message with the quotation agent"""
    try:
        # Run the quotation agent with the user's message
        result = run_quotation_agent(message)

        # Return the agent's final output
        return result

    except Exception as e:
        print(f"Error processing message: {e}")
        return "I encountered an error while processing your message. Please try again."
