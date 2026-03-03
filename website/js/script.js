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

    function populateTable(dataArray)
    {
        const tableBody = document.getElementById("table-body");

        tableBody.innerHTML = "";

        //think the way I'm gonna do this is get transactions by user ID (HOW?)
        //then loop through all it gives me
        //sort from most recent to least recent if it's not already in that form
    }
})