/** @type {import('next').NextConfig} */
const nextConfig = {
  // Dockerコンテナ用のスタンドアロンビルドを有効化
  output: 'standalone',

  webpack: (config) => {
    // Live2Dモデルファイルの静的配信を有効化
    config.module.rules.push({
      test: /\.(model3\.json|moc3|physics3\.json|pose3\.json)$/,
      type: 'asset/resource',
    });
    return config;
  },
};

module.exports = nextConfig;
