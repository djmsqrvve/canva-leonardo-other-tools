/**
 * Basic Leonardo API Client Scaffold
 * Usage: Intended to be imported by scripts in `dev/creative` or `dev/brand`
 */

async function generateImage(prompt, modelId) {
    const apiKey = process.env.LEONARDO_API_KEY;
    if (!apiKey) throw new Error("Missing LEONARDO_API_KEY in environment variables");

    // 1. Trigger the generation
    const response = await fetch('https://cloud.leonardo.ai/api/rest/v1/generations', {
        method: 'POST',
        headers: {
            'accept': 'application/json',
            'content-type': 'application/json',
            'authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
            height: 1024,
            width: 1024,
            modelId: modelId || "6b645e3a-d64f-4341-a6d8-7a3690fbf042", // Default to a standard model if none provided
            prompt: prompt,
            num_images: 1
        })
    });

    if (!response.ok) {
        throw new Error(`Failed to generate image: ${response.statusText}`);
    }

    const data = await response.json();
    return data.sdGenerationJob; // Contains the generationId
}

module.exports = {
    generateImage
};
