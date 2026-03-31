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
                localStorage.setItem("isLoggedIn", "false")
                console.log(localStorage.getItem("isLoggedIn"));
                return;
            }
            
            localStorage.setItem("isLoggedIn", "true")
            localStorage.setItem("currentUserID", data.user_id)
            console.log(localStorage.getItem("isLoggedIn"));
            console.log(localStorage.getItem("currentUserID"));
            alert("Login successful! " + data.message);
            window.location.href = "index.html";
            console.log(localStorage.getItem("isLoggedIn"));
            console.log(localStorage.getItem("currentUserID"));
        });
    }

    //logout logic

    document.getElementById("logout-button").addEventListener("click", logout)

    function logout()
    {
        localStorage.setItem("isLoggedIn", "false")
        localStorage.setItem("currentUserID", "null")
        alert("You have been logged out.");
        window.location.href = "login.html";
        console.log(localStorage.getItem("isLoggedIn"));   
        console.log(localStorage.getItem("currentUserID"));     
    }

    //welcome message logic
    const welcome_message = document.getElementById("welcome-message");
    if(!Object.is(localStorage.getItem("currentUserID"), "null"))
    {
        welcome_message.innerHTML = `Hello, ${localStorage.getItem("currentUserID")}!`;
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

    //auto-populating table that pulls and displays a user's transactions
    async function populateTable()
    {
        const tableBody = document.getElementById("table-body");

        tableBody.innerHTML = "";

        const user_id = "1";

        const balanceurl = new URL("http://127.0.0.1:8000/transaction/balance");
        const transactionurl = new URL(`http://127.0.0.1:8000/transaction/${user_id}`);
        //const categoryurl = new URL("http://127.0.0.1:8000/categories");

        balanceurl.searchParams.append("user_id", user_id);

        const balres = await fetch(balanceurl, { method: "GET" });
        const transres = await fetch(transactionurl, { method: "GET" });
        //const catres = await fetch(categoryurl, { method: "GET" });

        if (!balres.ok || !transres.ok) 
        {
            const err = await balres.json();
            console.error(err);
            return;
        }

        const balance = await balres.json();
        const transactions = await transres.json();
        //const categories = await catres.json();

        // const categoryMap = {};
        //     categories.forEach(cat => {
        //     categoryMap[cat.id] = cat.name;
        // });

        transactions.forEach(transaction => {
        const row = tableBody.insertRow();

        const description = row.insertCell(0);
        const date = row.insertCell(1);
        const amount = row.insertCell(2);
        const type = row.insertCell(3);
        const category = row.insertCell(4);

        description.innerHTML = transaction.description;

        date.innerHTML = new Date(transaction.date).toLocaleDateString();

        const sign = transaction.is_income ? "+" : "-";

        amount.innerHTML = sign + transaction.amount.toLocaleString("en-US", {
            style: "currency",
            currency: "USD"
        });

        amount.style.color = transaction.is_income ? "green" : "red";

        type.innerHTML = transaction.is_income ? "Income" : "Expense";

        category.innerHTML = transaction.category_id;
        
        //category.innerHTML = categoryMap[transaction.category_id] || "Unknown";
        //will implement this once Jorge gets auth set up
        
        });
    }
    populateTable();
});