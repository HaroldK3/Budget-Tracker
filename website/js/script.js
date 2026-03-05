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