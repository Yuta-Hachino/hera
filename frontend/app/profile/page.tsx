'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth-context-firebase'
import {
  getUserProfile,
  getUserData,
  addUserTag,
  deleteUserTag,
  getUserArtifacts,
  deleteUserArtifact,
} from '@/lib/api-client'
import { useRouter } from 'next/navigation'

interface UserProfile {
  name: string
  email: string
  picture?: string
  age?: number
  location?: string
  personality_traits?: {
    openness?: number
    conscientiousness?: number
    extraversion?: number
    agreeableness?: number
    neuroticism?: number
  }
  user_image_path?: string
}

interface UserData {
  uid: string
  email?: string
  name?: string
  picture?: string
  age?: number
  location?: string
  personality_traits?: Record<string, number>
  tags?: string[]
  created_at?: string
  updated_at?: string
}

interface Artifact {
  session_id: string
  created_at?: string
  letter?: {
    content?: string
    from?: string
  }
  images?: {
    partner?: string
    children?: Array<{ name: string; image_path: string }>
  }
  trip_plan?: {
    destination?: string
    activities?: string[]
  }
}

const PERSONALITY_LABELS: Record<string, string> = {
  openness: '開放性',
  conscientiousness: '誠実性',
  extraversion: '外向性',
  agreeableness: '協調性',
  neuroticism: '情緒安定性'
}

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [userData, setUserData] = useState<UserData | null>(null)
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newTag, setNewTag] = useState('')
  const [isAddingTag, setIsAddingTag] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/')
      return
    }

    if (user) {
      fetchAllData()
    }
  }, [user, authLoading, router])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      // プロフィール情報とユーザーデータを並列取得（個別にエラーハンドリング）
      const [profileData, userDataResponse, artifactsData] = await Promise.all([
        getUserProfile().catch((err) => {
          console.error('プロフィール取得エラー:', err)
          return null
        }),
        getUserData().catch((err) => {
          console.error('ユーザーデータ取得エラー:', err)
          return null
        }),
        getUserArtifacts().catch((err) => {
          console.error('生成物取得エラー:', err)
          return { artifacts: [] }
        }),
      ])
      setProfile(profileData)
      setUserData(userDataResponse)
      setArtifacts(artifactsData?.artifacts || [])
    } catch (err) {
      console.error('データ取得エラー:', err)
      // エラーが発生してもページは表示する
    } finally {
      setLoading(false)
    }
  }

  const handleAddTag = async () => {
    if (!newTag.trim()) return

    try {
      setIsAddingTag(true)
      await addUserTag(newTag.trim())
      setNewTag('')
      // ユーザーデータを再取得
      const userDataResponse = await getUserData()
      setUserData(userDataResponse)
    } catch (err) {
      console.error('タグ追加エラー:', err)
      alert('タグの追加に失敗しました')
    } finally {
      setIsAddingTag(false)
    }
  }

  const handleDeleteTag = async (tag: string) => {
    if (!confirm(`タグ「${tag}」を削除しますか？`)) return

    try {
      await deleteUserTag(tag)
      // ユーザーデータを再取得
      const userDataResponse = await getUserData()
      setUserData(userDataResponse)
    } catch (err) {
      console.error('タグ削除エラー:', err)
      alert('タグの削除に失敗しました')
    }
  }

  const handleDeleteArtifact = async (sessionId: string) => {
    if (!confirm('この生成物を削除しますか？')) return

    try {
      await deleteUserArtifact(sessionId)
      // アーティファクトを再取得
      const artifactsData = await getUserArtifacts()
      setArtifacts(artifactsData.artifacts || [])
    } catch (err) {
      console.error('生成物削除エラー:', err)
      alert('生成物の削除に失敗しました')
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">読み込み中...</p>
        </div>
      </div>
    )
  }

  // データがない場合はユーザー情報からフォールバック
  const displayName = profile?.name || user?.displayName || 'ユーザー'
  const displayEmail = profile?.email || user?.email || ''
  const avatarUrl = profile?.user_image_path || profile?.picture || user?.photoURL || '/default-avatar.png'

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* ヘッダー部分 */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-8 py-12">
            <div className="flex items-center space-x-6">
              {/* アバター画像 */}
              <div className="relative">
                <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-white shadow-lg">
                  <img
                    src={avatarUrl}
                    alt={displayName}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = '/default-avatar.png'
                    }}
                  />
                </div>
              </div>

              {/* 基本情報 */}
              <div className="flex-1 text-white">
                <h1 className="text-3xl font-bold mb-2">{displayName}</h1>
                <p className="text-pink-100">{displayEmail}</p>
              </div>
            </div>
          </div>

          {/* プロフィール詳細 */}
          <div className="px-8 py-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">プロフィール情報</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 年齢 */}
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">🎂</span>
                  <h3 className="text-lg font-semibold text-gray-700">年齢</h3>
                </div>
                <p className="text-2xl font-bold text-purple-600">
                  {profile?.age ? `${profile.age}歳` : '未設定'}
                </p>
              </div>

              {/* 居住地 */}
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">📍</span>
                  <h3 className="text-lg font-semibold text-gray-700">居住地</h3>
                </div>
                <p className="text-2xl font-bold text-blue-600">
                  {profile?.location || '未設定'}
                </p>
              </div>
            </div>

            {/* 性格特性 */}
            {profile?.personality_traits && (
              <div className="mt-8">
                <div className="flex items-center space-x-3 mb-6">
                  <span className="text-3xl">✨</span>
                  <h3 className="text-xl font-bold text-gray-800">性格特性（ビッグファイブ）</h3>
                </div>

                <div className="space-y-4">
                  {Object.entries(profile.personality_traits).map(([key, value]) => {
                    if (value === undefined || value === null) return null

                    const percentage = Math.round(value * 100)
                    const label = PERSONALITY_LABELS[key] || key

                    return (
                      <div key={key} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold text-gray-700">{label}</span>
                          <span className="text-purple-600 font-bold">{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* 性格特性が未設定の場合 */}
            {!profile?.personality_traits && !profile?.age && !profile?.location && (
              <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
                <p className="text-yellow-800 mb-4">
                  プロフィール情報がまだ設定されていません
                </p>
                <button
                  onClick={() => router.push('/start')}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition font-semibold"
                >
                  体験を始めてプロフィールを作成
                </button>
              </div>
            )}

            {/* タグセクション */}
            <div className="mt-8">
              <div className="flex items-center space-x-3 mb-6">
                <span className="text-3xl">🏷️</span>
                <h3 className="text-xl font-bold text-gray-800">あなたの特徴タグ</h3>
              </div>

              {/* タグ一覧 */}
              <div className="flex flex-wrap gap-2 mb-4">
                {userData?.tags && userData.tags.length > 0 ? (
                  userData.tags.map((tag, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-r from-purple-100 to-pink-100 border border-purple-300 rounded-full px-4 py-2 flex items-center space-x-2 group"
                    >
                      <span className="text-purple-700 font-medium">{tag}</span>
                      <button
                        onClick={() => handleDeleteTag(tag)}
                        className="text-purple-500 hover:text-red-500 transition opacity-0 group-hover:opacity-100"
                        title="削除"
                      >
                        ×
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 italic">
                    タグはまだありません。体験を通じて自動的に追加されます。
                  </p>
                )}
              </div>

              {/* タグ追加フォーム */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="新しいタグを入力..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={isAddingTag}
                />
                <button
                  onClick={handleAddTag}
                  disabled={isAddingTag || !newTag.trim()}
                  className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAddingTag ? '追加中...' : '追加'}
                </button>
              </div>
            </div>

            {/* 生成物セクション */}
            <div className="mt-8">
              <div className="flex items-center space-x-3 mb-6">
                <span className="text-3xl">📦</span>
                <h3 className="text-xl font-bold text-gray-800">あなたの生成物</h3>
              </div>

              {artifacts && artifacts.length > 0 ? (
                <div className="space-y-4">
                  {artifacts.map((artifact) => (
                    <div
                      key={artifact.session_id}
                      className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-6"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="text-sm text-gray-500">
                          {artifact.created_at
                            ? new Date(artifact.created_at).toLocaleString('ja-JP')
                            : '日時不明'}
                        </div>
                        <button
                          onClick={() => handleDeleteArtifact(artifact.session_id)}
                          className="text-red-500 hover:text-red-700 transition text-sm font-semibold"
                        >
                          削除
                        </button>
                      </div>

                      {/* 手紙 */}
                      {artifact.letter?.content && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-gray-700 mb-2">
                            💌 {artifact.letter.from || '未来の家族'}からの手紙
                          </h4>
                          <p className="text-gray-600 bg-pink-50 p-4 rounded-lg">
                            {artifact.letter.content.substring(0, 200)}
                            {artifact.letter.content.length > 200 ? '...' : ''}
                          </p>
                        </div>
                      )}

                      {/* 画像 */}
                      {(artifact.images?.partner || artifact.images?.children) && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-gray-700 mb-2">🖼️ 生成画像</h4>
                          <div className="flex gap-2 flex-wrap">
                            {artifact.images.partner && (
                              <div className="text-sm text-gray-600">パートナー画像あり</div>
                            )}
                            {artifact.images.children && artifact.images.children.length > 0 && (
                              <div className="text-sm text-gray-600">
                                子ども画像 {artifact.images.children.length}件
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* 旅行計画 */}
                      {artifact.trip_plan?.destination && (
                        <div className="mb-4">
                          <h4 className="font-semibold text-gray-700 mb-2">✈️ 旅行計画</h4>
                          <p className="text-gray-600">
                            目的地: {artifact.trip_plan.destination}
                          </p>
                          {artifact.trip_plan.activities && (
                            <p className="text-gray-600 text-sm mt-1">
                              アクティビティ: {artifact.trip_plan.activities.join(', ')}
                            </p>
                          )}
                        </div>
                      )}

                      <div className="text-xs text-gray-400 mt-2">
                        セッションID: {artifact.session_id}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
                  <p className="text-gray-500 mb-4">生成物はまだありません</p>
                  <button
                    onClick={() => router.push('/start')}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition font-semibold"
                  >
                    体験を始める
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
