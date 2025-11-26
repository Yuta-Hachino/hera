'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import {
  getUserProfile,
  getUserData,
  addUserTag,
  deleteUserTag,
  getUserArtifacts,
  deleteUserArtifact,
} from '@/lib/api-client'
import { useRouter } from 'next/navigation'
import Header from '@/components/Header'

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
          <p className="mt-4 text-gray-600 font-medium">読み込み中...</p>
        </div>
      </div>
    )
  }

  const displayName = profile?.name || user?.displayName || 'ユーザー'
  const displayEmail = profile?.email || user?.email || ''
  const avatarUrl = profile?.user_image_path || profile?.picture || user?.photoURL || '/default-avatar.png'

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <Header />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          {/* ヘッダー部分 */}
          <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-rose-500 px-8 py-12 relative overflow-hidden">
            {/* 背景装飾 */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>

            <div className="relative flex items-center space-x-6">
              {/* アバター画像 */}
              <div className="relative group">
                <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-white shadow-2xl ring-4 ring-white/20">
                  <img
                    src={avatarUrl}
                    alt={displayName}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = '/default-avatar.png'
                    }}
                  />
                </div>
                <div className="absolute -bottom-2 -right-2 bg-green-500 w-8 h-8 rounded-full border-4 border-white"></div>
              </div>

              {/* 基本情報 */}
              <div className="flex-1 text-white">
                <h1 className="text-4xl font-bold mb-2 drop-shadow-lg">{displayName}</h1>
                <p className="text-pink-100 text-lg">{displayEmail}</p>
              </div>
            </div>
          </div>

          {/* プロフィール詳細 */}
          <div className="px-8 py-10">
            <div className="flex items-center mb-8">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-purple-300 to-transparent"></div>
              <h2 className="text-3xl font-bold text-gray-900 mx-6">プロフィール情報</h2>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-purple-300 to-transparent"></div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 年齢 */}
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 shadow-md hover:shadow-xl transition">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-12 h-12 bg-purple-200 rounded-full flex items-center justify-center">
                    <span className="text-2xl">🎂</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-700">年齢</h3>
                </div>
                <p className="text-3xl font-bold text-purple-600 pl-15">
                  {profile?.age ? `${profile.age}歳` : '未設定'}
                </p>
              </div>

              {/* 居住地 */}
              <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-6 shadow-md hover:shadow-xl transition">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-12 h-12 bg-blue-200 rounded-full flex items-center justify-center">
                    <span className="text-2xl">📍</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-700">居住地</h3>
                </div>
                <p className="text-3xl font-bold text-blue-600 pl-15">
                  {profile?.location || '未設定'}
                </p>
              </div>
            </div>

            {/* 性格特性 */}
            {profile?.personality_traits && Object.keys(profile.personality_traits).length > 0 && (
              <div className="mt-10">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-14 h-14 bg-gradient-to-r from-yellow-400 to-pink-400 rounded-full flex items-center justify-center">
                    <span className="text-3xl">✨</span>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-800">性格特性（ビッグファイブ）</h3>
                </div>

                <div className="space-y-4">
                  {Object.entries(profile.personality_traits).map(([key, value]) => {
                    if (value === undefined || value === null) return null

                    const percentage = Math.round(value * 100)
                    const label = PERSONALITY_LABELS[key] || key

                    return (
                      <div key={key} className="bg-gradient-to-r from-gray-50 to-white rounded-xl p-5 shadow-sm hover:shadow-md transition">
                        <div className="flex justify-between items-center mb-3">
                          <span className="font-bold text-gray-800 text-lg">{label}</span>
                          <span className="text-purple-600 font-bold text-xl">{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
                          <div
                            className="bg-gradient-to-r from-purple-500 via-pink-500 to-rose-500 h-full rounded-full transition-all duration-700 ease-out shadow-lg"
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
              <div className="mt-10 bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-2xl p-8 text-center shadow-lg">
                <div className="text-6xl mb-4">💫</div>
                <p className="text-yellow-900 text-lg mb-6 font-medium">
                  プロフィール情報がまだ設定されていません
                </p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-4 rounded-xl hover:shadow-2xl transition font-bold text-lg transform hover:scale-105"
                >
                  体験を始めてプロフィールを作成
                </button>
              </div>
            )}

            {/* タグセクション */}
            <div className="mt-12">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-14 h-14 bg-gradient-to-r from-green-400 to-teal-400 rounded-full flex items-center justify-center">
                  <span className="text-3xl">🏷️</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-800">あなたの特徴タグ</h3>
              </div>

              {/* タグ一覧 */}
              <div className="flex flex-wrap gap-3 mb-6">
                {userData?.tags && userData.tags.length > 0 ? (
                  userData.tags.map((tag, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-r from-purple-100 to-pink-100 border-2 border-purple-300 rounded-full px-5 py-2 flex items-center space-x-2 group shadow-sm hover:shadow-md transition"
                    >
                      <span className="text-purple-700 font-semibold">{tag}</span>
                      <button
                        onClick={() => handleDeleteTag(tag)}
                        className="text-purple-500 hover:text-red-500 transition opacity-0 group-hover:opacity-100 font-bold text-lg"
                        title="削除"
                      >
                        ×
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 italic py-4">
                    タグはまだありません。体験を通じて自動的に追加されます。
                  </p>
                )}
              </div>

              {/* タグ追加フォーム */}
              <div className="flex gap-3">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="新しいタグを入力..."
                  className="flex-1 px-5 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  disabled={isAddingTag}
                />
                <button
                  onClick={handleAddTag}
                  disabled={isAddingTag || !newTag.trim()}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-3 rounded-xl hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed font-semibold transform hover:scale-105"
                >
                  {isAddingTag ? '追加中...' : '追加'}
                </button>
              </div>
            </div>

            {/* 生成物セクション */}
            <div className="mt-12">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-14 h-14 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center">
                  <span className="text-3xl">📦</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-800">あなたの生成物</h3>
              </div>

              {artifacts && artifacts.length > 0 ? (
                <div className="space-y-6">
                  {artifacts.map((artifact) => (
                    <div
                      key={artifact.session_id}
                      className="bg-gradient-to-br from-white to-gray-50 border-2 border-gray-200 rounded-2xl p-6 shadow-md hover:shadow-xl transition"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="text-sm text-gray-500 font-medium">
                          📅 {artifact.created_at
                            ? new Date(artifact.created_at).toLocaleString('ja-JP')
                            : '日時不明'}
                        </div>
                        <button
                          onClick={() => handleDeleteArtifact(artifact.session_id)}
                          className="text-red-500 hover:text-red-700 transition text-sm font-bold px-4 py-2 rounded-lg hover:bg-red-50"
                        >
                          🗑️ 削除
                        </button>
                      </div>

                      {/* 手紙 */}
                      {artifact.letter?.content && (
                        <div className="mb-4">
                          <h4 className="font-bold text-gray-800 mb-3 text-lg">
                            💌 {artifact.letter.from || '未来の家族'}からの手紙
                          </h4>
                          <p className="text-gray-700 bg-gradient-to-r from-pink-50 to-rose-50 p-5 rounded-xl leading-relaxed shadow-sm">
                            {artifact.letter.content.substring(0, 200)}
                            {artifact.letter.content.length > 200 ? '...' : ''}
                          </p>
                        </div>
                      )}

                      {/* 画像 */}
                      {(artifact.images?.partner || artifact.images?.children) && (
                        <div className="mb-4">
                          <h4 className="font-bold text-gray-800 mb-2">🖼️ 生成画像</h4>
                          <div className="flex gap-3 flex-wrap">
                            {artifact.images.partner && (
                              <div className="bg-blue-50 px-4 py-2 rounded-lg text-sm text-blue-700 font-medium">
                                パートナー画像あり
                              </div>
                            )}
                            {artifact.images.children && artifact.images.children.length > 0 && (
                              <div className="bg-pink-50 px-4 py-2 rounded-lg text-sm text-pink-700 font-medium">
                                子ども画像 {artifact.images.children.length}件
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* 旅行計画 */}
                      {artifact.trip_plan?.destination && (
                        <div className="mb-4">
                          <h4 className="font-bold text-gray-800 mb-2">✈️ 旅行計画</h4>
                          <p className="text-gray-700 font-medium">
                            目的地: {artifact.trip_plan.destination}
                          </p>
                          {artifact.trip_plan.activities && (
                            <p className="text-gray-600 text-sm mt-1">
                              アクティビティ: {artifact.trip_plan.activities.join(', ')}
                            </p>
                          )}
                        </div>
                      )}

                      <div className="text-xs text-gray-400 mt-4 pt-4 border-t border-gray-200">
                        セッションID: {artifact.session_id}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200 rounded-2xl p-12 text-center shadow-lg">
                  <div className="text-6xl mb-4">📭</div>
                  <p className="text-gray-600 text-lg mb-6 font-medium">生成物はまだありません</p>
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-4 rounded-xl hover:shadow-2xl transition font-bold text-lg transform hover:scale-105"
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
