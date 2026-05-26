// Chronos AI Frontend - app.js

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const chatMessages = document.getElementById("chatMessages");
    const sendBtn = document.getElementById("sendBtn");
    const statusBadge = document.getElementById("statusBadge");

    // 1. 서버 연동 상태 확인 (API Status)
    checkServerStatus();

    async function checkServerStatus() {
        try {
            const response = await fetch("/api/status");
            if (!response.ok) throw new Error("네트워크 응답 에러");
            
            const data = await response.json();
            const statusLabel = statusBadge.querySelector(".status-label");
            
            statusBadge.classList.remove("connected", "mock");
            
            if (data.google_calendar_connection === "connected") {
                statusBadge.classList.add("connected");
                statusLabel.textContent = "Google Calendar API 연결됨";
            } else {
                statusBadge.classList.add("mock");
                statusLabel.textContent = "가상 샌드박스 (Mock 모드)";
            }
        } catch (err) {
            console.error("서버 상태 조회를 실패했습니다:", err);
            const statusLabel = statusBadge.querySelector(".status-label");
            statusBadge.classList.add("mock");
            statusLabel.textContent = "서버 오프라인 (연결 실패)";
        }
    }

    // 2. 메시지 전송 이벤트 처리
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // 사용자 메시지 화면 출력
        appendMessage(text, "user");
        userInput.value = "";
        
        // 챗봇 대기 스피너 노출
        const spinner = appendTypingIndicator();
        scrollToBottom();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text })
            });

            // 스피너 제거
            spinner.remove();

            if (!response.ok) {
                throw new Error("서버 에러가 발생했습니다.");
            }

            const data = await response.json();
            
            // 챗봇 답변 텍스트 출력
            appendMessage(data.reply, "bot", data.action, data.result);
            
            // 실시간 상태 리프레시
            checkServerStatus();

        } catch (err) {
            spinner.remove();
            appendMessage(`⚠️ 통신 중 오류가 발생했습니다. 서버가 구동 중인지 확인해 주세요. (${err.message})`, "bot");
        }
        
        scrollToBottom();
    });

    // 3. 메시지 카드 동적 바인딩 함수
    function appendMessage(text, sender, action = "CHAT", actionResult = null) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", sender);

        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("message-avatar");
        
        if (sender === "user") {
            avatarDiv.innerHTML = '<i class="fa-solid fa-user"></i>';
        } else if (sender === "bot") {
            avatarDiv.innerHTML = '<i class="fa-solid fa-robot"></i>';
        } else {
            avatarDiv.innerHTML = '<i class="fa-solid fa-bell"></i>';
        }

        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        
        // 마크다운 줄바꿈 변환 적용
        const formattedText = text.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        contentDiv.innerHTML = `<p>${formattedText}</p>`;

        // 액션이 있는 경우 추가 캘린더 전용 카드 렌더링
        if (actionResult && actionResult.success) {
            if (action === "ADD" && actionResult.event) {
                const ev = actionResult.event;
                const card = createCalendarCard("일정 등록 완료", ev.summary, ev.start.dateTime, ev.end.dateTime, ev.description, ev.htmlLink);
                contentDiv.appendChild(card);
            } else if (action === "DELETE" && actionResult.deleted_event) {
                const ev = actionResult.deleted_event;
                const card = createCalendarCard("일정 삭제 취소", ev.summary, ev.start.dateTime, ev.end.dateTime, ev.description, ev.htmlLink);
                contentDiv.appendChild(card);
            }
        }

        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    // 캘린더 카드 생성기
    function createCalendarCard(badgeText, title, start, end, description, link) {
        const card = document.createElement("div");
        card.classList.add("calendar-card");

        const formattedStart = formatISOString(start);
        const formattedEnd = formatISOString(end);

        card.innerHTML = `
            <div class="calendar-card-header">
                <span class="calendar-title">
                    <i class="fa-solid fa-calendar-check"></i> ${title}
                </span>
                <span style="font-size:10px; color: var(--accent-glow); background: rgba(0,255,204,0.1); padding: 2px 6px; border-radius: 4px;">
                    ${badgeText}
                </span>
            </div>
            <div class="calendar-card-body">
                <div class="calendar-info-row">
                    <i class="fa-regular fa-clock"></i>
                    <span>시작: ${formattedStart}</span>
                </div>
                <div class="calendar-info-row">
                    <i class="fa-regular fa-circle-right"></i>
                    <span>종료: ${formattedEnd}</span>
                </div>
                ${description ? `
                <div class="calendar-info-row">
                    <i class="fa-regular fa-comment-dots"></i>
                    <span>설명: ${description}</span>
                </div>` : ''}
            </div>
            ${link ? `
            <div class="calendar-card-footer">
                <a href="${link}" target="_blank" class="calendar-link-btn">
                    구글 캘린더로 보기 <i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
            </div>` : ''}
        `;
        return card;
    }

    // ISO 타임스탬프 파싱 및 포맷팅 (YYYY년 MM월 DD일 HH:MM)
    function formatISOString(isoStr) {
        try {
            const date = new Date(isoStr);
            if (isNaN(date.getTime())) return isoStr;
            
            const y = date.getFullYear();
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const d = String(date.getDate()).padStart(2, '0');
            const h = String(date.getHours()).padStart(2, '0');
            const min = String(date.getMinutes()).padStart(2, '0');
            
            return `${y}년 ${m}월 ${d}일 ${h}시 ${min}분`;
        } catch (e) {
            return isoStr;
        }
    }

    // 대기 스피너
    function appendTypingIndicator() {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", "bot", "indicator-msg");

        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("message-avatar");
        avatarDiv.innerHTML = '<i class="fa-solid fa-robot"></i>';

        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        
        contentDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        return msgDiv;
    }

    // 스크롤 포커싱
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

// 가이드 칩 클릭 시 입력 매핑
function useExample(btn) {
    const text = btn.innerText.replace(/"/g, "");
    const userInput = document.getElementById("userInput");
    userInput.value = text;
    userInput.focus();
}
