# Guide: Docker Integration and n8n Routing

This guide provides a detailed roadmap for integrating Docker into your n8n project and a conceptual project to help you understand n8n's core routing capabilities.

## Part 1: Understanding and Running Your Dockerized n8n Project

Your project is already set up to use Docker. The `docker-compose.yml` file orchestrates the entire setup.

### Analysis of Your `docker-compose.yml`

Your `docker-compose.yml` file defines three main services:

1.  **`n8n`**: The core n8n application.
    *   `image: n8nio/n8n`: Uses the official n8n Docker image.
    *   `ports: - "5678:5678"`: Makes the n8n web interface available on your computer at `http://localhost:5678`.
    *   `volumes: - ./n8n_data:/home/node/.n8n`: Links a local `n8n_data` folder to the container to persist your workflows and credentials.
    *   `environment`: Sets up basic username/password authentication.
    *   `depends_on: - postgres`: Ensures the database starts before n8n.

2.  **`postgres`**: The PostgreSQL database n8n uses to store its data.

3.  **`ollama`**: A service that runs Ollama, allowing you to use large language models (LLMs) locally within your n8n workflows.

### Roadmap for Setup and Execution

**Prerequisite: Install Docker**

Ensure you have Docker Desktop installed and running on your computer.

**Step 1: Configure Environment Variables**

A `.env` file was created from the `.env.example` to manage your configuration securely.

**Step 2: Generate and Set the Encryption Key**

A unique, 32-character `N8N_ENCRYPTION_KEY` was generated and set in your `.env` file. This is a critical security setting used to encrypt your credentials within n8n.

**Step 3: Start the n8n Application**

To start your n8n instance, run the following command in your project directory:
```bash
docker-compose up -d
```

**Step 4: Access n8n**

Access the n8n user interface by navigating to: [http://localhost:5678](http://localhost:5678)

The default credentials are:
*   **Username:** `admin`
*   **Password:** `admin`

**Step 5: Stopping the Application**

When you are finished, you can stop all the services with this command:
```bash
docker-compose down
```

---

## Part 2: Conceptual Project: Multi-Agent Routing for Learning n8n

This project simulates a customer support system to teach the core concepts of routing in n8n.

### Project Goal

Create an n8n workflow that receives a customer inquiry, determines its topic, and routes it to the appropriate simulated agent.

### Core n8n Concepts You Will Learn

*   **Webhook Node:** Triggering a workflow from an external source.
*   **Switch Node:** The fundamental node for routing based on multiple conditions.
*   **Set Node:** Creating or modifying data within your workflow.

### The Workflow Structure

1.  **Webhook (Trigger):** Receives a JSON object with a "topic" and a "message".
    ```json
    {
      "topic": "billing",
      "message": "I have a question about my last invoice."
    }
    ```
2.  **Switch (Router):** Routes the workflow based on the `topic` field.
    *   `topic` == "billing"  -> Output 0
    *   `topic` == "technical" -> Output 1
    *   Default -> Output 2
3.  **Agent Branches (Routes):**
    *   **Branch 0 (Billing):** A Set node creates a billing-specific response.
    *   **Branch 1 (Technical):** A Set node creates a technical support response.
    *   **Branch 2 (General):** A Set node creates a general inquiry response.

### Workflow JSON

You can import this entire workflow by copying the JSON below and pasting it into a new workflow in the n8n editor.

```json
{
  "name": "Customer Support Routing",
  "nodes": [
    {
      "parameters": {},
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [ 250, 300 ]
    },
    {
      "parameters": { "path": "support-inquiry", "options": {} },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [ 400, 300 ],
      "webhookId": "your-webhook-id"
    },
    {
      "parameters": {
        "field": "={{$json[\"topic\"]}}",
        "rules": [
          { "value": "billing", "operator": "equals" },
          { "value": "technical", "operator": "equals" }
        ]
      },
      "name": "Switch",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 1,
      "position": [ 600, 300 ]
    },
    {
      "parameters": {
        "values": { "string": [ { "name": "Response", "value": "This is the billing department. How can I help with your invoice?" } ] },
        "options": {}
      },
      "name": "Billing Agent",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [ 800, 200 ]
    },
    {
      "parameters": {
        "values": { "string": [ { "name": "Response", "value": "This is technical support. Please provide more details about the issue." } ] },
        "options": {}
      },
      "name": "Technical Support Agent",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [ 800, 300 ]
    },
    {
      "parameters": {
        "values": { "string": [ { "name": "Response", "value": "Your question has been forwarded to our general inquiries team." } ] },
        "options": {}
      },
      "name": "General Inquiries Agent",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [ 800, 400 ]
    }
  ],
  "connections": {
    "Start": { "main": [ [ { "node": "Webhook", "type": "main", "index": 0 } ] ] },
    "Webhook": { "main": [ [ { "node": "Switch", "type": "main", "index": 0 } ] ] },
    "Switch": {
      "main": [
        [ { "node": "Billing Agent", "type": "main", "index": 0 } ],
        [ { "node": "Technical Support Agent", "type": "main", "index": 1 } ],
        [ { "node": "General Inquiries Agent", "type": "main", "index": 2 } ]
      ]
    }
  }
}
```
