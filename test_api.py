import requests

BASE_URL = "http://127.0.0.1:5000"


def test_get_products():
    url = f"{BASE_URL}/api/products"
    response = requests.get(url)
    print("Response text:", response.text)  # Debugging line
    response_json = response.json()
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response_json
    assert isinstance(data, list), "Expected data to be a list"
    print("test_get_products passed")

def test_get_users():
    url = f"{BASE_URL}/api/users"
    response = requests.get(url)
    print("Response text:", response.text)  # Debugging line
    response_json = response.json()
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response_json
    assert isinstance(data, list), "Expected data to be a list"
    print("test_get_users passed")

def test_get_user():
    acct_id = "shriram"  # Replace with a valid acct_id from your CSV
    url = f"{BASE_URL}/api/user/{acct_id}"
    response = requests.get(url)
    print("Response text:", response.text)  # Debugging line
    response_json = response.json()
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response_json
    assert isinstance(data, dict), "Expected data to be a dictionary"
    print("test_get_user passed")

def test_chatbot_assistance():
    url = f"{BASE_URL}/chatbot"
    data = {
        "query": "I need help with my network",
        "acct_id": "shriram",  # Replace with a valid acct_id from your CSV
        "history": []
    }
    response = requests.post(url, json=data)
    print("Response text:", response.text)  # Debugging line
    response_json = response.json()
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response_json
    assert "error" not in data, f"Unexpected error in response: {data.get('error')}"
    print("test_chatbot_assistance passed")

def test_upload_video():
    url = f"{BASE_URL}/upload_video"
    video_base64 = "..."  # Replace with a valid base64 encoded video string
    data = {
        "video": video_base64
    }
    response = requests.post(url, json=data)
    print("Response text:", response.text)  # Debugging line
    response_json = response.json()
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response_json
    assert "error" not in data, f"Unexpected error in response: {data.get('error')}"
    print("test_upload_video passed")

if __name__ == "__main__":
    test_get_products()
    test_get_users()
    test_get_user()
    test_chatbot_assistance()
    test_upload_video()
