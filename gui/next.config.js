/** @type {import('next').NextConfig} */

console.log('process.env.CAMUNDA_URL', process.env.CAMUNDA_URL)
const CAMUNDA_URL = process.env.CAMUNDA_URL

const nextConfig = {
  basePath: "/dashboard",
  experimental: {
    serverComponentsExternalPackages: ['hammerjs'],
  },
  rewrites: async () => {
    return [
      {
        source: '/api/engine/:path*',
        destination: `${CAMUNDA_URL}/:path*`,
      },
    ]
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.externals.push({ bufferutil: 'bufferutil', 'utf-8-validate': 'utf-8-validate' })
    }
    config.externals.push('pino-pretty', 'encoding')
    return config
  },
  env: {
    CAMUNDA_URL: CAMUNDA_URL,
  },
}

module.exports = nextConfig
