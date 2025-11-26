/**
 * APIクライアント
 * Firebase JWTトークンを自動的に付与してバックエンドAPIを呼び出す
 */
import { getAccessToken } from './firebase'
import { API_URL } from './config'

const API_BASE_URL = API_URL

interface RequestOptions extends RequestInit {
  requireAuth?: boolean
}

/**
 * APIリクエストを送信
 * @param endpoint エンドポイント（/api/...）
 * @param options リクエストオプション
 * @returns レスポンスJSON
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requireAuth = false, ...fetchOptions } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  }

  // 認証が必要な場合はJWTトークンを付与
  if (requireAuth) {
    const token = await getAccessToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || `API error: ${response.status}`)
  }

  return response.json()
}

/**
 * セッション作成
 */
export async function createSession(requireAuth: boolean = false) {
  return apiRequest('/api/sessions', {
    method: 'POST',
    requireAuth,
  })
}

/**
 * メッセージ送信
 */
export async function sendMessage(
  sessionId: string,
  message: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
    requireAuth,
  })
}

/**
 * セッション状態取得
 */
export async function getSessionStatus(
  sessionId: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/status`, {
    method: 'GET',
    requireAuth,
  })
}

/**
 * セッション完了
 */
export async function completeSession(
  sessionId: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/complete`, {
    method: 'POST',
    requireAuth,
  })
}

/**
 * 家族エージェントへメッセージ送信
 */
export async function sendFamilyMessage(
  sessionId: string,
  message: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/family/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
    requireAuth,
  })
}

/**
 * 家族エージェントの状態取得
 */
export async function getFamilyStatus(
  sessionId: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/family/status`, {
    method: 'GET',
    requireAuth,
  })
}

/**
 * ユーザー画像アップロード
 */
export async function uploadUserPhoto(
  sessionId: string,
  file: File,
  requireAuth: boolean = false
) {
  const formData = new FormData()
  formData.append('file', file)

  const token = requireAuth ? await getAccessToken() : null
  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/photos/user`,
    {
      method: 'POST',
      body: formData,
      headers,
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || `Upload error: ${response.status}`)
  }

  return response.json()
}

/**
 * パートナー画像生成
 */
export async function generatePartnerImage(
  sessionId: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/generate-image`, {
    method: 'POST',
    body: JSON.stringify({ target: 'partner' }),
    requireAuth,
  })
}

/**
 * 子ども画像生成
 */
export async function generateChildImage(
  sessionId: string,
  requireAuth: boolean = false
) {
  return apiRequest(`/api/sessions/${sessionId}/generate-child-image`, {
    method: 'POST',
    requireAuth,
  })
}

/**
 * ユーザープロフィール取得
 */
export async function getUserProfile() {
  return apiRequest('/api/profile', {
    method: 'GET',
    requireAuth: true,
  })
}

/**
 * ユーザーデータ取得（usersコレクションから）
 */
export async function getUserData() {
  return apiRequest('/api/users/me', {
    method: 'GET',
    requireAuth: true,
  })
}

/**
 * ユーザーデータ更新
 */
export async function updateUserData(data: {
  name?: string
  age?: number
  location?: string
  personality_traits?: Record<string, number>
}) {
  return apiRequest('/api/users/me', {
    method: 'PUT',
    body: JSON.stringify(data),
    requireAuth: true,
  })
}

/**
 * ユーザータグ追加
 */
export async function addUserTag(tag: string) {
  return apiRequest('/api/users/me/tags', {
    method: 'POST',
    body: JSON.stringify({ tag }),
    requireAuth: true,
  })
}

/**
 * ユーザータグ削除
 */
export async function deleteUserTag(tag: string) {
  return apiRequest('/api/users/me/tags', {
    method: 'DELETE',
    body: JSON.stringify({ tag }),
    requireAuth: true,
  })
}

/**
 * ユーザーの生成物一覧取得
 */
export async function getUserArtifacts() {
  return apiRequest('/api/users/me/artifacts', {
    method: 'GET',
    requireAuth: true,
  })
}

/**
 * ユーザーの生成物削除
 */
export async function deleteUserArtifact(sessionId: string) {
  return apiRequest(`/api/users/me/artifacts/${sessionId}`, {
    method: 'DELETE',
    requireAuth: true,
  })
}
