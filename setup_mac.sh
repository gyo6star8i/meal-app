#!/bin/bash
# =====================================================
# 급식알리미 맥북 개발환경 자동 설치 스크립트
# 사용법: bash setup_mac.sh
# =====================================================

set -e  # 오류 발생 시 중단

echo ""
echo "🍱 급식알리미 맥북 개발환경 설정 시작"
echo "================================================="

# ── 1. Homebrew 확인 / 설치 ──────────────────────────
if ! command -v brew &>/dev/null; then
  echo "📦 Homebrew 설치 중..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Apple Silicon(M1/M2/M3) 경로 설정
  if [[ $(uname -m) == "arm64" ]]; then
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
else
  echo "✅ Homebrew 이미 설치됨"
fi

# ── 2. Python 확인 / 설치 ───────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "🐍 Python 설치 중..."
  brew install python
else
  echo "✅ Python $(python3 --version) 이미 설치됨"
fi

# ── 3. Node.js 확인 / 설치 (Claude Code용) ──────────
if ! command -v node &>/dev/null; then
  echo "📗 Node.js 설치 중..."
  brew install node
else
  echo "✅ Node.js $(node --version) 이미 설치됨"
fi

# ── 4. Claude Code 설치 ─────────────────────────────
if ! command -v claude &>/dev/null; then
  echo "🤖 Claude Code 설치 중..."
  npm install -g @anthropic-ai/claude-code
else
  echo "✅ Claude Code 이미 설치됨"
fi

# ── 5. Python 가상환경 생성 & 패키지 설치 ───────────
echo "📦 Python 가상환경 생성 중..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ 패키지 설치 완료"

# ── 6. Streamlit secrets 설정 ───────────────────────
mkdir -p .streamlit
if [ ! -f .streamlit/secrets.toml ]; then
  echo ""
  echo "🔑 Groq API 키를 입력하세요 (https://console.groq.com 에서 발급)"
  read -p "GROQ_API_KEY: " GROQ_KEY
  if [ -n "$GROQ_KEY" ]; then
    cat > .streamlit/secrets.toml << EOF
GROQ_API_KEY = "$GROQ_KEY"
EOF
    echo "✅ .streamlit/secrets.toml 생성 완료"
  else
    echo "⚠️  API 키를 입력하지 않았습니다. 나중에 .streamlit/secrets.toml 에 직접 입력하세요."
  fi
else
  echo "✅ .streamlit/secrets.toml 이미 존재"
fi

# ── 7. 완료 메시지 ───────────────────────────────────
echo ""
echo "================================================="
echo "🎉 설치 완료!"
echo ""
echo "▶  앱 실행 방법:"
echo "   source venv/bin/activate"
echo "   streamlit run app.py"
echo ""
echo "▶  브라우저에서 http://localhost:8501 열기"
echo "================================================="
