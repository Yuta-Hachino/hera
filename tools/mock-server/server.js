const jsonServer = require('json-server');
const server = jsonServer.create();
const router = jsonServer.router('db.json');
const middlewares = jsonServer.defaults();
const cors = require('cors');

// CORS設定
server.use(cors());

// デフォルトミドルウェア（logger, static, cors, no-cache）
server.use(middlewares);

// リクエストボディのパース
server.use(jsonServer.bodyParser);

// カスタムルート: シミュレーション実行
server.post('/api/v1/simulate', (req, res) => {
  const { user_data } = req.body;

  // モックレスポンス
  res.json({
    session_id: `session_${Date.now()}`,
    status: 'processing',
    message: 'Family simulation started',
    estimated_time: 30,
    data: {
      user_profile: user_data,
      family_members_count: 3,
      story_generated: false,
      image_generated: false
    }
  });
});

// カスタムルート: ストーリー生成
server.post('/api/v1/stories/generate', (req, res) => {
  const { session_id, scenario } = req.body;

  res.json({
    story_id: `story_${Date.now()}`,
    session_id,
    title: '未来の家族の一日',
    content: 'あなたの未来の家族は、笑顔あふれる素敵な日々を過ごしています...',
    scene: scenario || 'daily_life',
    status: 'completed',
    created_at: new Date().toISOString()
  });
});

// カスタムルート: 手紙生成
server.post('/api/v1/letters/generate', (req, res) => {
  const { session_id, from_member } = req.body;

  res.json({
    letter_id: `letter_${Date.now()}`,
    session_id,
    from: from_member || 'child',
    subject: '大好きなパパ・ママへ',
    content: 'いつもありがとう！大好きだよ！',
    illustration_url: '/mock/images/child-drawing.png',
    status: 'completed',
    created_at: new Date().toISOString()
  });
});

// カスタムルート: 画像生成
server.post('/api/v1/images/generate', (req, res) => {
  const { session_id, prompt, style } = req.body;

  res.json({
    image_id: `image_${Date.now()}`,
    session_id,
    url: '/mock/images/generated-family.png',
    prompt,
    style: style || 'realistic',
    status: 'completed',
    created_at: new Date().toISOString()
  });
});

// カスタムルート: ヘルスチェック
server.get('/api/v1/health', (req, res) => {
  res.json({
    status: 'healthy',
    version: '1.0.0',
    mock: true,
    timestamp: new Date().toISOString(),
    services: {
      database: 'ok',
      redis: 'ok',
      ai_service: 'ok'
    }
  });
});

// 遅延レスポンスのミドルウェア（リアルなAPI動作をシミュレート）
server.use((req, res, next) => {
  setTimeout(next, 300); // 300msの遅延
});

// JSON Serverのルーターを使用
server.use('/api/v1', router);

// サーバー起動
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`🚀 Mock API Server is running on http://localhost:${PORT}`);
  console.log(`📝 Resources available at:`);
  console.log(`   - http://localhost:${PORT}/api/v1/users`);
  console.log(`   - http://localhost:${PORT}/api/v1/sessions`);
  console.log(`   - http://localhost:${PORT}/api/v1/stories`);
  console.log(`   - http://localhost:${PORT}/api/v1/letters`);
  console.log(`   - http://localhost:${PORT}/api/v1/images`);
  console.log(`   - http://localhost:${PORT}/api/v1/health`);
  console.log(`\n💡 Custom endpoints:`);
  console.log(`   - POST http://localhost:${PORT}/api/v1/simulate`);
  console.log(`   - POST http://localhost:${PORT}/api/v1/stories/generate`);
  console.log(`   - POST http://localhost:${PORT}/api/v1/letters/generate`);
  console.log(`   - POST http://localhost:${PORT}/api/v1/images/generate`);
});
