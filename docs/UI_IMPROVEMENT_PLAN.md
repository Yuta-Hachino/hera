# UI改善計画
**Atlassian Design System原則に基づく段階的な改善提案**

**作成日**: 2025年11月7日
**対象**: AIファミリー・シミュレーター フロントエンド

---

## エグゼクティブサマリー

現在のUIはTailwind CSSでカスタムスタイリングされていますが、以下の課題があります：
- ❌ 一貫性のないデザインパターン（ボタンスタイル、色使い）
- ❌ アクセシビリティへの配慮不足
- ❌ デザイントークンの欠如
- ❌ 再利用可能なコンポーネントが不十分

Atlassian Design Systemの原則を適用し、**段階的に改善**します。

---

## 現状分析

### 現在の実装状況

#### ページ構成
| ページ | 主な課題 |
|--------|---------|
| `/` (ログイン) | グラデーション背景が派手、エラー表示が目立たない |
| `/chat/[sessionId]` | プログレス表示が小さい、メッセージ区別が不明瞭 |
| `/family/[sessionId]` | 情報密度が高い、階層構造が不明瞭 |

#### コンポーネント
| コンポーネント | 課題 |
|--------------|------|
| `ChatMessage` | スピーカー区別が弱い、タイムスタンプ表示なし |
| `ChatInput` | フォーカス状態が不明瞭、送信ボタンのアクセシビリティ |
| `LoadingSpinner` | サイズバリエーション不足、アクセシビリティラベル欠如 |
| `ProfileProgress` | プログレス表示が小さく見づらい |

#### スタイリングの問題
```tsx
// ❌ 問題例1: インラインスタイルが散在
className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"

// ❌ 問題例2: 一貫性のない色使い
// ログインページ: from-blue-50 to-indigo-100
// チャットページ: from-primary-500 to-pink-500
// 家族ページ: from-amber-500 to-pink-500
```

---

## Atlassian Design Systemから学ぶべき原則

### 1. デザイントークンの活用

**定義**:
```css
/* Spacing */
--ds-space-050: 4px
--ds-space-100: 8px
--ds-space-200: 16px
--ds-space-300: 24px
--ds-space-400: 32px

/* Colors */
--ds-background-neutral: #F4F5F7
--ds-text: #172B4D
--ds-text-subtle: #6B778C
--ds-border: #DFE1E6

/* Radius */
--ds-radius-small: 3px
--ds-radius-medium: 6px
--ds-radius-large: 12px
```

**適用**:
- カスタムCSS変数を定義し、一貫したスペーシング・色使いを実現
- Tailwind configに統合

### 2. コンポーネントの再利用性

**原則**:
> "Components are reusable building blocks that meet specific interaction needs."

**適用**:
- `Button`コンポーネント（primary, secondary, subtle, danger）
- `TextField`コンポーネント（統一されたフォーカススタイル）
- `Banner`/`InlineMessage`（エラー・成功メッセージ）

### 3. アクセシビリティファースト

**重要なポイント**:
- **Focus ring**: キーボード操作時の視覚的フィードバック
- **ARIAラベル**: スクリーンリーダー対応
- **カラーコントラスト**: WCAG AA準拠（最低4.5:1）

---

## 改善計画（3フェーズアプローチ）

### Phase 1: デザイントークンとベースコンポーネント（2週間）

#### 1.1 デザイントークンの定義

**ファイル**: `frontend/styles/design-tokens.css`
```css
:root {
  /* Spacing System */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Color System */
  /* Primary - Hera Theme */
  --color-primary-50: #FFF5F7;
  --color-primary-100: #FFE3E8;
  --color-primary-500: #FF1744;  /* メインカラー */
  --color-primary-600: #D50032;
  --color-primary-700: #AB0029;

  /* Neutrals */
  --color-neutral-0: #FFFFFF;
  --color-neutral-50: #F9FAFB;
  --color-neutral-100: #F3F4F6;
  --color-neutral-500: #6B7280;
  --color-neutral-900: #111827;

  /* Semantic Colors */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #3B82F6;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

  /* Focus Ring (Accessibility) */
  --focus-ring: 0 0 0 3px rgba(59, 130, 246, 0.5);
}
```

**Tailwind統合**: `tailwind.config.js`
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'var(--color-primary-50)',
          500: 'var(--color-primary-500)',
          // ...
        },
      },
      spacing: {
        xs: 'var(--space-xs)',
        sm: 'var(--space-sm)',
        // ...
      },
    },
  },
}
```

#### 1.2 ベースコンポーネントの作成

##### Button コンポーネント
**ファイル**: `frontend/components/ui/Button.tsx`

```tsx
import { ButtonHTMLAttributes, ReactNode } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  // ベーススタイル
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary-500 text-white hover:bg-primary-600 focus-visible:ring-primary-500',
        secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 focus-visible:ring-neutral-500',
        subtle: 'bg-transparent hover:bg-neutral-100 text-neutral-700 focus-visible:ring-neutral-500',
        danger: 'bg-error text-white hover:bg-red-600 focus-visible:ring-error',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  children: ReactNode;
}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={buttonVariants({ variant, size, className })}
      {...props}
    />
  );
}
```

**使用例**:
```tsx
// Before
<button className="w-full bg-green-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300 transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
  情報収集完了 - 次へ進む
</button>

// After
<Button variant="primary" size="lg" className="w-full">
  情報収集完了 - 次へ進む
</Button>
```

##### TextField コンポーネント
**ファイル**: `frontend/components/ui/TextField.tsx`

```tsx
import { InputHTMLAttributes, forwardRef } from 'react';

export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            w-full px-3 py-2 border rounded-md
            bg-white text-neutral-900
            placeholder:text-neutral-400
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            disabled:bg-neutral-50 disabled:text-neutral-500
            ${error ? 'border-error' : 'border-neutral-300'}
            ${className}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? 'error-message' : helperText ? 'helper-text' : undefined}
          {...props}
        />
        {error && (
          <p id="error-message" className="mt-1 text-sm text-error" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id="helper-text" className="mt-1 text-sm text-neutral-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

TextField.displayName = 'TextField';
```

##### Banner / InlineMessage コンポーネント
**ファイル**: `frontend/components/ui/Banner.tsx`

```tsx
import { ReactNode } from 'react';
import { XMarkIcon, CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

type BannerVariant = 'success' | 'warning' | 'error' | 'info';

export interface BannerProps {
  variant: BannerVariant;
  children: ReactNode;
  onDismiss?: () => void;
}

const variantStyles: Record<BannerVariant, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const icons: Record<BannerVariant, typeof CheckCircleIcon> = {
  success: CheckCircleIcon,
  warning: ExclamationTriangleIcon,
  error: ExclamationTriangleIcon,
  info: InformationCircleIcon,
};

export function Banner({ variant, children, onDismiss }: BannerProps) {
  const Icon = icons[variant];

  return (
    <div
      className={`flex items-start gap-3 p-4 border rounded-lg ${variantStyles[variant]}`}
      role="alert"
      aria-live="polite"
    >
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">{children}</div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="flex-shrink-0 hover:opacity-70 transition-opacity"
          aria-label="閉じる"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
```

**使用例**:
```tsx
// Before
<div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
  {error}
</div>

// After
<Banner variant="error">{error}</Banner>
```

##### LoadingSpinner コンポーネント（改善）
**ファイル**: `frontend/components/ui/LoadingSpinner.tsx`

```tsx
import { cva, type VariantProps } from 'class-variance-authority';

const spinnerVariants = cva(
  'animate-spin rounded-full border-b-2',
  {
    variants: {
      size: {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12',
      },
      color: {
        primary: 'border-primary-500',
        neutral: 'border-neutral-500',
        white: 'border-white',
      },
    },
    defaultVariants: {
      size: 'md',
      color: 'primary',
    },
  }
);

export interface LoadingSpinnerProps extends VariantProps<typeof spinnerVariants> {
  label?: string;
}

export function LoadingSpinner({ size, color, label = '読み込み中' }: LoadingSpinnerProps) {
  return (
    <div className="flex items-center justify-center" role="status">
      <div className={spinnerVariants({ size, color })} aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
}
```

#### 1.3 インストール必要なパッケージ

```bash
npm install class-variance-authority clsx tailwind-merge
npm install @heroicons/react  # アイコン用
```

---

### Phase 2: ページレイアウトの改善（2週間）

#### 2.1 ログインページのリファクタリング

**課題**:
- グラデーション背景が派手
- エラー表示が目立たない
- フォーカス状態が不明瞭

**改善案**:
```tsx
// frontend/app/page.tsx (改善版の一部)
export default function LoginPage() {
  // ... (ロジックは同じ)

  return (
    <div className="flex items-center justify-center min-h-screen bg-neutral-50">
      <div className="max-w-md w-full space-y-6 p-8 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-neutral-900 mb-2">
            AIファミリー・シミュレーター
          </h1>
          <p className="text-neutral-600">
            未来の家族を体験しましょう
          </p>
        </div>

        <div className="mt-8 space-y-4">
          {error && (
            <Banner variant="error" onDismiss={() => setError(null)}>
              {error}
            </Banner>
          )}

          <Button
            onClick={handleGoogleLogin}
            disabled={isLoggingIn}
            variant="secondary"
            size="lg"
            className="w-full"
          >
            {isLoggingIn ? (
              <>
                <LoadingSpinner size="sm" color="neutral" />
                <span>ログイン中...</span>
              </>
            ) : (
              <>
                <GoogleIcon className="w-5 h-5" />
                <span>Googleアカウントでログイン</span>
              </>
            )}
          </Button>

          <p className="text-xs text-neutral-500 text-center">
            ログインすることで、
            <a href="/terms" className="text-primary-500 hover:text-primary-600 underline">
              利用規約
            </a>
            と
            <a href="/privacy" className="text-primary-500 hover:text-primary-600 underline">
              プライバシーポリシー
            </a>
            に同意したものとみなされます。
          </p>
        </div>
      </div>
    </div>
  );
}
```

#### 2.2 チャットページの改善

**課題**:
- メッセージの区別が不明瞭
- プログレスバーが小さい
- スタイル切り替えボタンが目立たない

**改善案**:
```tsx
// ChatMessageコンポーネントの改善
export function ChatMessage({ speaker, message, timestamp }: ConversationMessage) {
  const isUser = speaker === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`
          max-w-[70%] px-4 py-3 rounded-lg
          ${isUser
            ? 'bg-primary-500 text-white rounded-br-none'
            : 'bg-neutral-100 text-neutral-900 rounded-bl-none'
          }
        `}
      >
        {!isUser && (
          <div className="text-xs font-semibold mb-1 text-primary-600">
            {speaker === 'hera' ? 'ヘーラー' : speaker}
          </div>
        )}
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        {timestamp && (
          <div className={`text-xs mt-1 ${isUser ? 'text-white/70' : 'text-neutral-500'}`}>
            {new Date(timestamp).toLocaleTimeString('ja-JP', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        )}
      </div>
    </div>
  );
}
```

**プログレスバーの改善**:
```tsx
// ProfileProgressコンポーネントの改善
export function ProfileProgress({ progress }: { progress: InformationProgress }) {
  const totalFields = Object.keys(progress).length;
  const completedFields = Object.values(progress).filter(Boolean).length;
  const percentage = totalFields > 0 ? (completedFields / totalFields) * 100 : 0;

  return (
    <div className="px-4 py-3 bg-white border-b border-neutral-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-neutral-700">情報収集の進捗</span>
        <span className="text-sm font-semibold text-primary-500">
          {completedFields} / {totalFields}
        </span>
      </div>
      <div className="w-full bg-neutral-200 rounded-full h-3">
        <div
          className="bg-primary-500 h-3 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={completedFields}
          aria-valuemin={0}
          aria-valuemax={totalFields}
          aria-label="情報収集の進捗"
        />
      </div>
    </div>
  );
}
```

#### 2.3 家族会話ページの改善

**課題**:
- 情報密度が高い
- 旅行プランメモが埋もれている
- 手紙の表示が地味

**改善案**:
```tsx
// 旅行プランメモの改善
<div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-sm">
  <h2 className="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-2">
    <MapPinIcon className="w-4 h-4 text-primary-500" />
    旅行プランメモ
  </h2>
  <div className="space-y-2 text-sm">
    <div className="flex items-start gap-2">
      <span className="font-medium text-neutral-700 min-w-[80px]">行きたい場所:</span>
      <span className="text-neutral-900">{tripInfo?.destination || '未定'}</span>
    </div>
    <div className="flex items-start gap-2">
      <span className="font-medium text-neutral-700 min-w-[80px]">やりたいこと:</span>
      <span className="text-neutral-900">
        {(tripInfo?.activities && tripInfo.activities.length > 0)
          ? tripInfo.activities.join('、')
          : '未定'}
      </span>
    </div>
  </div>
</div>

// 手紙の表示改善
{familyPlan?.letter && (
  <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-300 rounded-lg p-6 shadow-md">
    <div className="flex items-center gap-2 mb-4">
      <EnvelopeIcon className="w-6 h-6 text-amber-600" />
      <h2 className="text-lg font-bold text-amber-900">未来の家族からの手紙</h2>
    </div>
    <div className="bg-white/80 rounded-md p-4">
      <p className="text-sm text-neutral-800 whitespace-pre-line leading-relaxed">
        {familyPlan.letter}
      </p>
    </div>
  </div>
)}
```

---

### Phase 3: アクセシビリティとUX改善（1週間）

#### 3.1 キーボードナビゲーション

**実装**:
```tsx
// ChatInputコンポーネントの改善
export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message);
      setMessage('');
      textareaRef.current?.focus(); // 送信後にフォーカスを戻す
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Shift + Enterで改行、Enterのみで送信
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <TextField
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'メッセージを入力...'}
        disabled={disabled}
        aria-label="メッセージ入力"
      />
      <Button
        type="submit"
        disabled={disabled || !message.trim()}
        aria-label="メッセージを送信"
      >
        <PaperAirplaneIcon className="w-5 h-5" />
      </Button>
    </form>
  );
}
```

#### 3.2 スクリーンリーダー対応

**追加すべきARIA属性**:
```tsx
// ローディング状態
<div role="status" aria-live="polite" aria-busy={isLoading}>
  <LoadingSpinner label="読み込み中..." />
</div>

// エラーメッセージ
<div role="alert" aria-live="assertive">
  <Banner variant="error">{error}</Banner>
</div>

// プログレスバー
<div
  role="progressbar"
  aria-valuenow={completedFields}
  aria-valuemin={0}
  aria-valuemax={totalFields}
  aria-label="情報収集の進捗"
/>
```

#### 3.3 カラーコントラストの検証

**ツール**: Lighthouse, axe DevTools

**改善例**:
```css
/* Before: コントラスト比 3.2:1 (不合格) */
.text-gray-500 { color: #6B7280; }  /* on white background */

/* After: コントラスト比 4.7:1 (合格) */
--color-neutral-600: #4B5563;
.text-neutral-600 { color: var(--color-neutral-600); }
```

#### 3.4 フォーカスインジケーターの強化

**グローバルスタイル追加**:
```css
/* frontend/styles/globals.css */
*:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* ボタンにはリングスタイル */
button:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}
```

---

## 実装優先順位

### 高優先度（Phase 1） - 2週間
1. ✅ デザイントークンの定義
2. ✅ `Button`コンポーネント
3. ✅ `TextField`コンポーネント
4. ✅ `Banner`コンポーネント
5. ✅ `LoadingSpinner`改善

**影響**: 全ページのボタン・フォーム・エラー表示が統一される

### 中優先度（Phase 2） - 2週間
6. ✅ ログインページのリファクタリング
7. ✅ チャットページの改善
8. ✅ 家族会話ページの改善
9. ✅ `ProfileProgress`コンポーネント改善

**影響**: 主要ページのUXが大幅に向上

### 低優先度（Phase 3） - 1週間
10. ✅ キーボードナビゲーション強化
11. ✅ ARIA属性の追加
12. ✅ カラーコントラスト検証・修正
13. ✅ フォーカスインジケーター強化

**影響**: アクセシビリティが向上、WCAG AA準拠に近づく

---

## 成功指標（KPI）

### 定量指標
| 指標 | 現状 | 目標 |
|------|------|------|
| Lighthouse Accessibility Score | 未計測 | 90以上 |
| カラーコントラスト不合格箇所 | 未計測 | 0件 |
| コンポーネント再利用率 | 低（推定30%） | 80%以上 |
| インラインスタイル行数 | 高（推定500行） | 50%削減 |

### 定性指標
- ✅ デザインの一貫性が向上
- ✅ ユーザーがボタンの役割を直感的に理解できる
- ✅ キーボードだけで全操作が可能
- ✅ エラーメッセージが見やすく、対処方法が明確

---

## リスクと対策

### リスク1: 既存UIの破壊
**対策**:
- 段階的な移行（1ページずつ）
- 旧コンポーネントとの並行運用期間を設ける
- スタイルガイドページを作成して動作確認

### リスク2: 開発工数の増加
**対策**:
- Phase 1のみ優先実施
- 残りは余裕があれば実施
- コンポーネントライブラリの選択肢も検討（shadcn/ui等）

### リスク3: パフォーマンスへの影響
**対策**:
- CSS変数はパフォーマンスに影響しない
- コンポーネント分割によりバンドルサイズは微増するが許容範囲
- Lazy loadingで対応

---

## 次のステップ

### 即座に開始可能
1. デザイントークンの定義ファイル作成
2. `Button`コンポーネントの実装
3. ログインページへの適用

### 追加検討事項
1. **コンポーネントライブラリの採用**
   - shadcn/ui（Radix UI + Tailwind）
   - Headless UI（TailwindチームのUIライブラリ）
   - メリット: 開発スピードアップ、アクセシビリティ担保
   - デメリット: カスタマイズ性の制約

2. **Storybookの導入**
   - コンポーネントカタログの作成
   - デザイナーとの協業がしやすくなる

3. **デザインシステムドキュメントの整備**
   - 使い方ガイド
   - コンポーネントの使い分け基準

---

## 参考資料

### Atlassian Design System
- Components: https://atlassian.design/components
- Accessibility: https://atlassian.design/foundations/accessibility
- Design Tokens: https://atlassian.design/foundations/design-tokens

### その他
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Material Design (参考): https://m3.material.io/
- Tailwind CSS Best Practices: https://tailwindcss.com/docs/

---

**作成者**: Claude Code
**最終更新**: 2025年11月7日
