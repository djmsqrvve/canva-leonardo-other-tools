# Leonardo AI API Overview & Open Source Findings

Based on the official documentation (`docs.leonardo.ai`), the Leonardo API is a standard REST API that allows you to programmatically trigger their generative AI models.

## Core Integration Details

- **Base URL:** `https://cloud.leonardo.ai/api/rest/v1/`
- **Authentication:** Bearer token using the `LEONARDO_API_KEY`.
- **Primary Endpoint:** `POST /generations` (To trigger a new image/video generation).

## Key Workflows for Internal Tools

1. **Text-to-Image Generation**
   - You send a prompt, negative prompt, model ID (e.g., Leonardo Kino XL), width, and height.
   - The API is asynchronous. You receive a `generationId`.
   - You must either **poll** `GET /generations/{id}` or set up a **Webhook** to get the final image URLs.

2. **Custom Model Training (LoRA)**
   - You can upload a dataset of images via the API.
   - Trigger a training job to create a custom model fine-tuned on your specific brand assets (useful for the `brand` directory).
   - Once trained, you pass this custom `modelId` into the `/generations` endpoint.

3. **Visual-to-Code**
   - The Leonardo web app has a "Get API Code" feature. Designers can tweak settings in the UI until they get the perfect image, then export the exact JSON payload required to reproduce that style via the API.

## Code Example Pattern

```javascript
// Example of initiating a generation
const response = await fetch('https://cloud.leonardo.ai/api/rest/v1/generations', {
  method: 'POST',
  headers: {
    'accept': 'application/json',
    'content-type': 'application/json',
    'authorization': `Bearer ${process.env.LEONARDO_API_KEY}`
  },
  body: JSON.stringify({
    height: 1024,
    width: 1024,
    modelId: "6b645e3a-d64f-4341-a6d8-7a3690fbf042", // Example model
    prompt: "A futuristic city skyline at sunset",
    num_images: 1
  })
});
```

## Resources
- **Documentation Hub:** https://docs.leonardo.ai/
- **API Access:** https://app.leonardo.ai/api-access
