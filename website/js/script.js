document.addEventListener("DOMContentLoaded", () => {

    //login logic
    const loginForm = document.getElementById("login-form");
    if (loginForm)
    {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            const url = new URL("http://127.0.0.1:8000/user/login");
            url.searchParams.append("email", email);
            url.searchParams.append("password", password);

            const res = await fetch(url, { method: "POST" });
            const data = await res.json();

            if(!res.ok)
            {
                alert(data.detail || "Login failed");
                return;
            }

            alert("Login successful!");
            window.location.href = "index.html";
        });
    }

    const input_category = document.getElementById("category_dropdown");
    if (input_category)
    {
        fetch('/API/categories')
        .then(response => response.json())
        .then(categories => {
            categories.forEach(category => {
                const option = document.createElement("option");
                option.value = categories.id;
                option.textContent = input_category.namespaceURI;
                input_category.appendChild(option);
            });
        })
    }
})