document.addEventListener("DOMContentLoaded", function () {
    // Handle forms
    const physiqueForm = document.getElementById("physiqueForm");
    if (physiqueForm) {
        physiqueForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            
            const button = document.getElementById("generateButton");
            button.disabled = true;
            button.innerHTML = 'Generating...';
            
            const formData = {
                weight: document.getElementById("weight").value,
                height: document.getElementById("height").value,
                age: document.getElementById("age").value,
                gender: document.getElementById("gender").value,
                diseases: document.getElementById("diseases").value || 'None'
            };

            try {
                const response = await fetch("/api/physique", {  
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (response.ok && data.plan) {
                    const resultDiv = document.getElementById("plan-result");
                    resultDiv.innerHTML = `<pre>${data.plan}</pre>`;
                    resultDiv.style.display = "block";
                } else {
                    throw new Error(data.error || "Failed to generate plan");
                }
            } catch (error) {
                console.error("Error:", error);
                alert(error.message);
            } finally {
                button.disabled = false;
                button.innerHTML = 'Generate Plan';
            }
        });
    }

    // ✅ Sign-in Form Submission
    const signinForm = document.getElementById("signin-form");
    if (signinForm) {
        signinForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const formData = {
                email: document.getElementById("email").value.trim(),
                password: document.getElementById("password").value
            };

            try {
                const response = await fetch("/api/signin", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert(errorData.error || "Login failed. Please try again.");
                    return;
                }

                const result = await response.json();
                if (result.user) {
                    localStorage.setItem("auth_token", result.user.id);  // Store user ID as token
                    const nextUrl = new URLSearchParams(window.location.search).get("next") || "/";
                    window.location.href = nextUrl;
                }
            } catch (error) {
                console.error("Login error:", error);
                alert("Network error. Please check your connection and try again.");
            }
        });
    }

    // ✅ Logout Handler
    const logoutButton = document.getElementById("logout-button");
    if (logoutButton) {
        logoutButton.addEventListener("click", async function () {
            try {
                // Call server-side logout endpoint
                const response = await fetch("/api/logout", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    }
                });

                if (response.ok) {
                    localStorage.removeItem("auth_token");
                    window.location.href = "/";
                } else {
                    alert("Logout failed. Please try again.");
                }
            } catch (error) {
                console.error("Logout error:", error);
                alert("Logout failed. Please try again.");
            }
        });
    }

    // ✅ BMI Calculator (Requires Authentication)
    const bmiForm = document.getElementById("bmiForm");
    if (bmiForm) {
        bmiForm.addEventListener("submit", function (e) {
            e.preventDefault();

            const weight = parseFloat(document.getElementById("weight").value);
            const height = parseFloat(document.getElementById("height").value) / 100;

            if (weight <= 0 || height <= 0) {
                alert("Please enter valid positive numbers for weight and height.");
                return;
            }

            const bmi = weight / (height * height);
            const category = bmi < 18.5 ? "Underweight" :
                           bmi < 25   ? "Normal weight" :
                           bmi < 30   ? "Overweight" : "Obese";

            document.getElementById("bmiValue").textContent = bmi.toFixed(1);
            document.getElementById("bmiCategory").textContent = category;
            document.getElementById("result").style.display = "block";
        });
    }

    // ✅ Chatbot (Requires Authentication)
    const chatForm = document.getElementById("chat-form");
    if (chatForm) {
        chatForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const userInput = document.getElementById("user-input");
            const message = userInput.value.trim();
            const thinking = document.getElementById("thinking");

            if (!message) return;

            // Add user message
            addMessage(message, true);
            userInput.value = "";

            // Show thinking animation
            thinking.style.display = "flex";

            try {
                const response = await fetch("/api/chatbot", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ message })
                });

                // Hide thinking animation
                thinking.style.display = "none";

                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.href = "/signin";
                        return;
                    }
                    throw new Error("Failed to get response");
                }

                const data = await response.json();
                addMessage(data.response);

            } catch (error) {
                thinking.style.display = "none";
                addMessage("Sorry, something went wrong. Please try again.");
            }
        });

        function addMessage(text, isUser = false) {
            const chatMessages = document.getElementById("chat-messages");
            const messageDiv = document.createElement("div");
            messageDiv.className = `message ${isUser ? "user" : "bot"}`;

            const content = document.createElement("div");
            content.className = "message-content";
            content.textContent = text;

            messageDiv.appendChild(content);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
});