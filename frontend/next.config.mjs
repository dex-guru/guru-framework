/** @type {import('next').NextConfig} */

const dotenv = require('dotenv');
dotenv.config();
console.log('Loaded Environment Variables:', process.env);

const nextConfig = {
  experimental: { instrumentationHook: true, esmExternals: 'loose' },
  images: {
    formats: ['image/webp'],
    minimumCacheTTL: 2592000,
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
      },
      { protocol: 'https', hostname: 'img.burning.meme', pathname: '/images/*' },
      { protocol: 'https', hostname: '*.amazonaws.com' },
      { protocol: 'https', hostname: '*.amazonaws.com' },
      { protocol: 'https', hostname: 'ipfs.io', pathname: '/ipfs/*' },
    ],
  },
  env: {
    AUTH_SECRET: process.env.AUTH_SECRET,
    FLOW_API_URL: process.env.FLOW_API_URL,
    SYS_KEY: process.env.SYS_KEY,
    AUTH_TRUST_HOST: process.env.AUTH_TRUST_HOST,
    WAREHOUSE_API_HOST: process.env.WAREHOUSE_API_HOST,
    WAREHOUSE_API_KEY: process.env.WAREHOUSE_API_KEY,
    LANGCHAIN_API_URL: process.env.LANGCHAIN_API_URL,
    LANGCHAIN_API_KEY: process.env.LANGCHAIN_API_KEY,
    NEXT_PUBLIC_PROJECT_ID: process.env.NEXT_PUBLIC_PROJECT_ID,
    NEXT_PUBLIC_API_HOST: process.env.NEXT_PUBLIC_API_HOST,
    NEXT_PUBLIC_APP_INTRO: process.env.NEXT_PUBLIC_APP_INTRO,
    NEXT_PUBLIC_APP_CURRENCY: process.env.NEXT_PUBLIC_APP_CURRENCY,
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
    NEXT_PUBLIC_APP_CHAIN_ID: process.env.NEXT_PUBLIC_APP_CHAIN_ID,
    NEXT_PUBLIC_APP_RPC_URL: process.env.NEXT_PUBLIC_APP_RPC_URL,
    NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS: process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS,
    NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL: process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL,
    NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME: process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME,
    NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL: process.env.NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL,
    NEXT_PUBLIC_APP_CHAIN_LABEL: process.env.NEXT_PUBLIC_APP_CHAIN_LABEL,
    NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES: process.env.NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES,
  },
}

const fullNextConfig = {
  webpack(config, { webpack, buildId }) {
    // Grab the existing rule that handles SVG imports
    const fileLoaderRule = config.module.rules.find((rule) => rule.test?.test?.('.svg'))

    config.module.rules.push(
      // Reapply the existing rule, but only for svg imports ending in ?url
      {
        ...fileLoaderRule,
        test: /\.svg$/i,
        resourceQuery: /url/, // *.svg?url
      },
      // Convert all other *.svg imports to React components
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule.issuer,
        resourceQuery: { not: [...fileLoaderRule.resourceQuery.not, /url/] }, // exclude if *.svg?url
        use: ['@svgr/webpack'],
      }
    )

    // Modify the file loader rule to ignore *.svg, since we have it handled now.
    fileLoaderRule.exclude = /\.svg$/i

    config.plugins.push(
      new webpack.DefinePlugin({
        'process.env.GIT_COMMIT': JSON.stringify(buildId),
      })
    )

    config.externals.push('pino-pretty', 'lokijs', 'encoding')

    return config
  },
  generateBuildId: async () => {
    // Use a fixed ID for non-Git builds, or create a unique one
    return 'build-' + Date.now().toString();
  },

  ...nextConfig,
}

export default fullNextConfig
