from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import base64

app = Flask(__name__)
CORS(app)
@app.route('/')
def index():
  return render_template('index.html')

# Load the product catalog and user information from CSV with error handling
try:
    product_catalog = pd.read_csv('Enhanced_Product_Catalog.csv')
    product_catalog['Connectivity Speed (Mbps)'] = pd.to_numeric(
        product_catalog['Connectivity Speed (Mbps)'], errors='coerce'
    )
    product_catalog = product_catalog.dropna(subset=['Connectivity Speed (Mbps)'])
except Exception as e:
    print(f"Error loading Enhanced_Product_Catalog.csv: {e}")
    product_catalog = pd.DataFrame()

try:
    user_info = pd.read_csv('current_customers.csv')
except Exception as e:
    print(f"Error loading current_customers.csv: {e}")
    user_info = pd.DataFrame()

@app.route('/api/connectivity', methods=['GET'])
def get_connectivity():
    return jsonify({product_catalog})

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Get the product catalog.
    """
    if product_catalog.empty:
        return jsonify({"error": "Product catalog not available"}), 500
    return jsonify(product_catalog.to_dict(orient='records'))

@app.route('/api/users', methods=['GET'])
def get_users():
    """
    Get the user information.
    """
    if user_info.empty:
        return jsonify({"error": "User information not available"}), 500
    return jsonify(user_info.to_dict(orient='records'))

@app.route('/api/user/<acct_id>', methods=['GET'])
def get_user(acct_id):
    """
    Get information for a specific user.
    """
    user_data = user_info[user_info['acct_id'] == acct_id].to_dict(orient='records')
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_data[0])

# SambaNova API Configurations
SAMBA_API_URL = "https://api.sambanova.ai/v1/chat/completions"
SAMBA_API_KEY = "8607c80a-b115-4eb2-bb39-d70a73c43e53"

# Helper function to call SambaNova API
def call_sambanova_api(model, messages):
    """
    Call SambaNova API for recommendations.
    """
    headers = {"Authorization": f"Bearer {SAMBA_API_KEY}"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "top_p": 0.1
    }
    try:
        response = requests.post(SAMBA_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Route for Chatbot Assistance
@app.route('/api/chatbot', methods=['POST'])
def chatbot_assistance():
    """
    AI-based chatbot for network troubleshooting and product recommendations.
    """
    try:
        user_query = request.json.get("query")
        acct_id = request.json.get("acct_id")
        history = request.json.get("history", [])

        # Check if product catalog is empty
        if product_catalog.empty:
            return jsonify({"error": "Product catalog not available"}), 500

        # Fetch user-specific information
        user_data = user_info[user_info['acct_id'] == acct_id].to_dict(orient='records')
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        user_data = user_data[0]

        # Parse user's current network speed
        current_speed = float(user_data['network_speed'].replace('M', '').replace('G', '').strip())
        if "G" in user_data['network_speed']:
            current_speed *= 1000  # Convert Gbps to Mbps

        # Filter product catalog for better plans
        better_plans = product_catalog[product_catalog['Connectivity Speed (Mbps)'] > current_speed].sort_values(by='Price')

        # Generate tailored recommendations
        recommendations = []
        for _, row in better_plans.iterrows():
            recommendations.append({
                "Product Name": row['Product Name'],
                "Speed": f"{row['Connectivity Speed (Mbps)']} Mbps",
                "Price": f"${row['Price']}/mo",
                "Router Type": row['Router Type']
            })

        # Construct recommendations text
        recommendations_text = "Here are alternative plans for your needs:\n"
        for rec in recommendations[:3]:  # Limit to top 3 recommendations
            recommendations_text += f"- **{rec['Product Name']}**: Speed: {rec['Speed']}, Price: {rec['Price']}, Router Type: {rec['Router Type']}.\n"

        # Construct chat history text
        history_text = "\n".join([f"User: {msg['user']}\nAssistant: {msg.get('assistant', '')}" for msg in history])

        # Construct the user context
        user_context = f"""
        User Information:
        Account ID: {acct_id}
        Extenders: {user_data['extenders']}
        Wireless Clients: {user_data['wireless_clients_count']}
        Wired Clients: {user_data['wired_clients_count']}
        RX Bandwidth (bps): {user_data['rx_avg_bps']}
        TX Bandwidth (bps): {user_data['tx_avg_bps']}
        Network Speed: {user_data['network_speed']}
        RSSI Mean: {user_data['rssi_mean']}
        RSSI Min: {user_data['rssi_min']}
        RSSI Max: {user_data['rssi_max']}
        
        Plan Recommendations:
        {recommendations_text}
        """

        # Construct the prompt
        prompt = f"""
        The user is asking for help with their network issues and better internet plans. Based on the provided query, network data, and chat history, give a conversational and friendly response that:
        
        1. Explains the issue in simple terms.
        2. Provides clear, actionable steps the user can take.
        3. Recommends alternative internet plans or extenders based on their current plan and needs.
        4. Avoids overly technical language and focuses on practical advice.

        User Query: {user_query}

        Context:
        {user_context}

        Chat History:
        {history_text}

        Make sure the response is supportive, concise, and easy to understand.
        """

        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        response = call_sambanova_api("Meta-Llama-3.2-3B-Instruct", messages)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for Video Upload and Integration with AR
@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """
    Upload video, analyze it using SambaNova API, and integrate with AR recommendations.
    """
    try:
        data = request.get_json()
        video_base64 = data.get('video')
        if not video_base64:
            return jsonify({"error": "No video provided"}), 400

        # Call SambaNova API to analyze video
        response = analyze_video_with_sambanova(video_base64)
        if "error" in response:
            return jsonify({"error": response["error"]}), 500

        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def analyze_video_with_sambanova(video_base64):
    """
    Analyze the uploaded video using SambaNova API.
    """
    headers = {"Authorization": f"Bearer {SAMBA_API_KEY}"}
    payload = {
        "model": "Llama-3.2-11B-Vision-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this video for room dimensions and obstructions."},
                    {"type": "image_url", "image_url": {"url": f"data:video/mp4;base64,{video_base64}"}}
                ]
            }
        ]
    }

    response = requests.post(SAMBA_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

if __name__ == '__main__':
    app.run(port=5000)
