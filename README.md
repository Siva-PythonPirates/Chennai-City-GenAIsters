# Project Raseed - Team Chennai-City-GenAIsters

This project is a proof-of-concept for an AI-powered, agent-driven marketplace. It creates a seamless e-commerce experience where a Buyer Agent and a Merchant Agent negotiate transactions in real-time, orchestrated by a secure backend and experienced through a cross-platform Flutter application.

## 📝 Project Overview

The core challenge is to move beyond simple, static e-commerce transactions. This project builds "Project Raseed," an AI-powered platform that acts as a comprehensive financial and purchasing assistant for everyday users. It simulates an entire marketplace ecosystem where AI agents, representing both buyers and merchants, interact to purchase goods, negotiate prices, and generate receipts, all while ensuring data integrity and a dynamic user experience.

---
## ✨ Core Features

* **Dual User Roles:** Users can sign up and choose to be either a **Buyer** or a **Merchant**, each with a dedicated dashboard and functionalities.
* **Product Management:** Merchants can list products for sale, set prices, and remove items from their inventory.
* **AI Agent Negotiation:** A real-time, dynamic conversation is generated for every transaction by two AI agents (Buyer and Merchant) who negotiate the final price based on predefined limits.
* **Secure Transactions:** All financial logic (wallet updates, stock changes, receipt generation) is handled securely by a Python/FastAPI backend, preventing client-side manipulation.
* **Real-time Updates:** Dashboards for both buyers and merchants update in real-time using Firestore streams, reflecting new sales and purchases instantly.
* **Cross-Platform:** Built with Flutter for a consistent experience on both Android and iOS.

---
## 🛠️ Architecture

The project is built on a modern, decoupled architecture:

* **Frontend:** A Flutter application for the user interface.
* **Backend:** A Python server using the **FastAPI** framework to handle business logic.
* **Database:** **Cloud Firestore** for real-time data storage (users, products, transactions).
* **Authentication:** **Firebase Authentication** with Google Sign-In.
* **AI Agents:** Powered by the **Google Generative AI (Gemini)** API, orchestrated by the Python backend.

---
## 🚀 Setup Instructions

Follow these steps to get the project running on your local machine.

### Prerequisites
* [Flutter SDK](https://flutter.dev/docs/get-started/install)
* [Python 3.8+](https://www.python.org/downloads/)
* [Firebase CLI](https://firebase.google.com/docs/cli)
* [ngrok](https://ngrok.com/download)

### Step 1: Firebase Project Setup
1.  **Create a Firebase Project:** Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2.  **Enable Services:**
    * **Authentication:** Go to the "Authentication" section, click "Get Started," and enable **Google** as a sign-in provider.
    * **Firestore Database:** Go to the "Firestore Database" section, click "Create database," and start in **Test Mode**.
3.  **Get Backend Credentials (`serviceAccountKey.json`):**
    * In your Firebase project settings (⚙️), go to **Service accounts**.
    * Click **"Generate new private key"**. A JSON file will be downloaded.
    * Rename this file to `serviceAccountKey.json` and place it in the root of your Python backend folder.
4.  **Get Frontend Credentials (`google-services.json`):**
    * In your Firebase project settings, go to the "General" tab.
    * Under "Your apps," add a new **Android** app. Use a package name like `com.example.raseed_agent_app`.
    * Follow the setup steps and download the `google-services.json` file.
    * Place this file inside the `android/app/` directory of your Flutter project.

### Step 2: Backend Setup (Python/FastAPI)
1.  Navigate to your backend project folder in the terminal.
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:** Create a `requirements.txt` file with the content below and run `pip install -r requirements.txt`.
    ```text
    fastapi
    uvicorn[standard]
    pydantic
    firebase-admin
    google-generativeai
    ```
4.  **Get your Gemini API Key:**
    * Go to [Google AI Studio](https://aistudio.google.com/) and create an API key.
    * **Set it as an environment variable** in your terminal before running the server. This is critical for security.
        * **Mac/Linux:** `export GOOGLE_API_KEY="YOUR_API_KEY"`
        * **Windows (CMD):** `set GOOGLE_API_KEY="YOUR_API_KEY"`

### Step 3: Frontend Setup (Flutter)
1.  Navigate to your Flutter project folder.
2.  Ensure the `google-services.json` file is in place.
3.  Run `flutter pub get` to install all dependencies.

---
## ▶️ How to Run the Project

1.  **Start the Backend Server:**
    In your backend folder's terminal (with the virtual environment activated and API key set), run:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
2.  **Expose the Backend with ngrok:**
    In a **new terminal window**, run `ngrok` to create a public URL for your local server.
    ```bash
    ngrok http 8000
    ```
    `ngrok` will give you a **`https://...` Forwarding URL**. Copy it.

3.  **Update the URL in Flutter:**
    * Open the `lib/transaction_view.dart` file.
    * Find the `_makeApiCall` function and paste your `ngrok` URL.
        ```dart
        final url = Uri.parse('https://YOUR_UNIQUE_ID.ngrok-free.app/execute-transaction/');
        ```
    * **IMPORTANT:** The first time you use a new `ngrok` URL, open it in a browser and click the "Visit Site" button to clear the one-time warning page.

4.  **Run the Flutter App:**
    In your Flutter project's terminal, run:
    ```bash
    flutter run
    ```

---
## 🔮 Future Enhancements

This project provides a strong foundation that can be extended to match the original "Project Raseed" vision.

* **Multimodal Receipt Ingestion:** Use Gemini's multimodal capabilities to allow users to scan physical receipts via photo or video to automatically populate their expense lists.
* **Spending Analysis & Financial Advice:** Analyze the collected transaction data to provide users with insights into their spending habits (e.g., "You've spent 20% more on groceries this month").
* **Google Wallet Integration:** Generate Google Wallet passes for digital receipts, shopping lists, or financial insights, creating a deeply integrated experience.
* **Advanced Inventory Management:** Allow merchants to track stock levels, get sales analytics, and receive AI-powered suggestions for what products to restock.
* **User & Product Reviews:** Implement a rating system for both buyers and merchants to build trust within the ecosystem.

## For previewing the app you can view the demo here: `https://drive.google.com/drive/folders/13_h2cRcyKFY3pqe29J5augQzNzy_wcyH?usp=sharing`
