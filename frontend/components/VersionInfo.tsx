'use client'

import { useEffect } from 'react'
import packageJson from '../package.json'

export default function VersionInfo() {
  useEffect(() => {
    // ビルド情報を作成（環境変数があればそれを優先、なければpackage.jsonから）
    const buildInfo = {
      version: process.env.NEXT_PUBLIC_VERSION || packageJson.version,
      buildTime: process.env.NEXT_PUBLIC_BUILD_TIME || new Date().toISOString(),
      environment: process.env.NODE_ENV,
      apiUrl: process.env.NEXT_PUBLIC_API_URL,
      revision: process.env.NEXT_PUBLIC_GIT_COMMIT || 'local',
    }

    // コンソールにバージョン情報を出力（スタイリング付き）
    console.log(
      '%c🚀 AI Family Simulator %c v' + buildInfo.version + ' ',
      'background: linear-gradient(to right, #667eea, #764ba2); color: white; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;',
      'background: #2d3748; color: #48bb78; padding: 4px 8px; border-radius: 0 4px 4px 0; font-weight: bold;'
    )

    console.log('%c📋 Build Information', 'color: #667eea; font-weight: bold; font-size: 12px;')
    console.table({
      'Version': buildInfo.version,
      'Build Time': new Date(buildInfo.buildTime).toLocaleString('ja-JP'),
      'Environment': buildInfo.environment,
      'API URL': buildInfo.apiUrl,
      'Git Commit': buildInfo.revision.substring(0, 7),
    })

    // グローバルに公開（デバッグ用）
    if (typeof window !== 'undefined') {
      (window as any).__APP_VERSION__ = buildInfo
    }
  }, [])

  return null
}