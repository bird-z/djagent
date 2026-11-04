#!/usr/bin/env bash
# 启动 kgJP 手机端服务。
#
# 为什么必须 setsid：
# 在 WorkBuddy 沙箱里用 nohup + & 启动的进程会被会话回收，
# 表现为「启动后几秒内 Connection refused」。setsid 让它脱离会话才活得久。

set -eu

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-/home/bird/.workbuddy/binaries/python/versions/3.13.12/bin/python3}"
PORT="${PORT:-8801}"
LOG="${LOG:-/tmp/kgjp_web.log}"

# 已有实例先清掉，避免端口占用
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    echo "端口 ${PORT} 已被占用，先停止旧进程"
    pkill -f "web.py --port ${PORT}" 2>/dev/null || true
    sleep 1
fi

cd "$DIR"

setsid "$PY" web.py --port "$PORT" > "$LOG" 2>&1 < /dev/null &
sleep 2

if curl -s --max-time 3 "http://127.0.0.1:${PORT}/health" | grep -q '"ok"'; then
    IP=$(ip -4 -o addr show wlp4s0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1)
    [ -z "$IP" ] && IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
    echo "✅ 已启动"
    echo "   本机:  http://127.0.0.1:${PORT}"
    echo "   手机:  http://${IP}:${PORT}"
    echo "   日志:  $LOG"
    echo ""
    echo "   停止: pkill -f 'web.py --port ${PORT}'"
else
    echo "❌ 启动失败，日志："
    tail -20 "$LOG"
    exit 1
fi
