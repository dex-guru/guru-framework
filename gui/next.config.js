/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: "/dashboard",
  experimental: {
    serverComponentsExternalPackages: ["hammerjs"],
  },
  rewrites: async () => {
    return [
      {
        source: "/app/engine/:path*",
        destination: "https://chainflow-engine.dexguru.biz/engine-rest/:path*",
      },
    ];
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.externals.push({
        bufferutil: "bufferutil",
        "utf-8-validate": "utf-8-validate",
      });
    }
    config.externals.push("pino-pretty", "encoding");

    return config;
  },
};

module.exports = nextConfig;
