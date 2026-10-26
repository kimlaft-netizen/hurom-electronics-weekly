const crypto = require('node:crypto');

const REPOSITORY = 'kimlaft-netizen/hurom-electronics-weekly';
const WORKFLOW = 'weekly.yml';
const SITE_ORIGIN = 'https://hurom-electronics-weekly.vercel.app';

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'POST 요청만 허용됩니다.' });
  }

  if (req.headers.origin !== SITE_ORIGIN) {
    return res.status(403).json({ error: '허용되지 않은 요청입니다.' });
  }

  const githubToken = process.env.GITHUB_TOKEN;
  const triggerPassword = process.env.UPDATE_TRIGGER_PASSWORD;
  if (!githubToken || !triggerPassword) {
    return res.status(503).json({ error: 'Vercel 환경 변수 설정이 필요합니다.' });
  }

  let password = req.body?.password;
  if (typeof req.body === 'string') {
    try {
      password = JSON.parse(req.body).password;
    } catch {
      return res.status(400).json({ error: '요청 형식이 올바르지 않습니다.' });
    }
  }

  if (typeof password !== 'string') {
    return res.status(401).json({ error: '승인 암호가 올바르지 않습니다.' });
  }
  const supplied = Buffer.from(password);
  const expected = Buffer.from(triggerPassword);
  if (supplied.length !== expected.length || !crypto.timingSafeEqual(supplied, expected)) {
    return res.status(401).json({ error: '승인 암호가 올바르지 않습니다.' });
  }

  try {
    const response = await fetch(
      `https://api.github.com/repos/${REPOSITORY}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: 'POST',
        headers: {
          Accept: 'application/vnd.github+json',
          Authorization: `Bearer ${githubToken}`,
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'hurom-electronics-weekly',
        },
        body: JSON.stringify({ ref: 'main' }),
      },
    );

    if (response.status !== 204) {
      return res.status(502).json({ error: 'GitHub Actions 실행 요청에 실패했습니다.' });
    }
    return res.status(202).json({ message: '주간 업데이트 실행을 요청했습니다.' });
  } catch {
    return res.status(502).json({ error: 'GitHub에 연결하지 못했습니다.' });
  }
};
