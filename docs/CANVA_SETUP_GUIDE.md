# Canva Setup Guide for CLI

Since we are building a CLI tool that runs on your local machine (outside of the Canva Editor) to automate design generation, you need to create an **Integration**.

## Steps to Create

1. Go to your Canva Developer Portal.
2. Click **"Your Integrations"** (Do not click "Your Apps").
3. Click **"Create an Integration"**.
4. Give it a name like "DJ MSQRVVE Brand Automator".
5. Under the **Authentication** section in your new integration, generate a Client ID and Client Secret.

For this local Python CLI, you will be using standard OAuth 2.0 to get an access token.