/**
 * Basic Canva Connect API Client Scaffold
 * Usage: Intended to be imported by scripts in `dev/helix` or `dev/creative`
 */

async function getCanvaAccessToken() {
    const clientId = process.env.CANVA_CLIENT_ID;
    const clientSecret = process.env.CANVA_CLIENT_SECRET;

    if (!clientId || !clientSecret) {
        throw new Error("Missing Canva credentials in environment variables");
    }

    // Typical OAuth2 Client Credentials flow (Implementation depends on Canva's specific Connect API auth flow)
    // For off-platform integrations, Canva Connect API uses standard OAuth 2.0.
    
    // Note: The specific token endpoint and parameters should follow the Canva Connect API docs:
    // https://www.canva.dev/docs/connect/authentication/
    
    throw new Error("getCanvaAccessToken is scaffolded. Implement OAuth 2.0 flow here.");
}

async function autofillTemplate(templateId, data) {
    const token = await getCanvaAccessToken();
    
    const response = await fetch(`https://api.canva.com/rest/v1/autofills`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            brand_template_id: templateId,
            data: data
        })
    });
    
    if (!response.ok) {
        throw new Error(`Failed to autofill template: ${response.statusText}`);
    }

    return response.json();
}

module.exports = {
    getCanvaAccessToken,
    autofillTemplate
};
