from IPython.display import Markdown, display, update_display
import ollama
import gradio as gr
import json

MODEL = 'llama3.2'

system_message = "You are a helpful assistant for an Airline called FlightAI. "
system_message += "Give short, courteous answers, no more than 1 sentence. "
system_message += "Always be accurate. If you don't know the answer, say so."

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = ollama.chat(model=MODEL, messages=messages)
    return response["message"]["content"]

gr.ChatInterface(fn=chat, type="messages").launch()

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499"}

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

# Define tool function for ticket pricing
price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": price_function}]

def handle_tool_call(message):
    tool_calls = message.get("tool_calls", [])
    if not tool_calls:
        return None, None  # No tool call found
    
    tool_call = tool_calls[0]  # Assume first tool call
    arguments = tool_call.function.arguments  # It's already a dict
    city = arguments.get("destination_city")
    price = get_ticket_price(city)
    
    response = {
        "role": "tool",
        "content": json.dumps({"destination_city": city, "price": price}),
    }
    return response, city


def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = ollama.chat(model=MODEL, messages=messages, tools=tools)

    print(response)  # Debugging step

    if "tool_calls" in response["message"]:
        message = response["message"]
        tool_response, city = handle_tool_call(message)

        if tool_response:
            messages.append(message)
            messages.append(tool_response)
            response = ollama.chat(model=MODEL, messages=messages)  # Call Ollama again

    return response["message"]["content"]

gr.ChatInterface(fn=chat, type="messages").launch()