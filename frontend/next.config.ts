import type { NextConfig } from "next";

// In Docker Compose we want the standard server build (SSR + API routes).
// In the aws-deploy stack the frontend is served from S3 + CloudFront, so
// we run a static export. NEXT_OUTPUT=export triggers that path —
// .github/workflows/deploy-aws.yml sets it before `next build`.
const isStaticExport = process.env.NEXT_OUTPUT === "export";

const nextConfig: NextConfig = {
  output: isStaticExport ? "export" : undefined,
  trailingSlash: isStaticExport,
  images: {
    unoptimized: isStaticExport,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  },
};

export default nextConfig;
