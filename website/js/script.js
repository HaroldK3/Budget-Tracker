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
            console.log(localStorage.getItem("isLoggedIn"));
            alert("Login successful!");
            window.location.href = "index.html";
            console.log(localStorage.getItem("isLoggedIn"));
        });
    }

    //logout logic

    document.getElementById("logoutButton").addEventListener("click", logout)

    function logout()
    {
        localStorage.setItem("isLoggedIn", "false")
        alert("You have been logged out.");
        window.location.href = "login.html";
        console.log(localStorage.getItem("isLoggedIn"));        
    }

    //getting categories
    const input_category = document.getElementById("category_dropdown");
    if (input_category)
    {
        fetch('http://127.0.0.1:8000/categories/?user_id=1')
        .then(response => response.json())
        .then(categories => {
            categories.forEach(category => {
                const option = document.createElement("option");
                option.value = category.id;
                //option.textContent = input_category.namespaceURI;
                option.textContent = category.name;
                input_category.appendChild(option);
            });
        })
    }
    
    //Add category
    const addCategoryButton = document.getElementById("addCategoryButton");
    if (addCategoryButton)
    {
        addCategoryButton.addEventListener("click", async () => {
            const user_id = 1;

            const name = document.getElementById("newCategoryName").value.trim();
            const type = document.getElementById("newCategoryType").value;

            if (!name) {
                alert("Please enter a category name.");
                return;
            }
            if (!type) {
                alert("Please select a category type.");
                return;
            }

            const url = new URL("http://127.0.0.1:8000/categories/");
            url.searchParams.append("user_id", user_id);

            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, type })
            });

            const data = await res.json();

            if (!res.ok)
            {
                alert(data.detail || "Failed to add category.");
                return;
            }

            alert("Category added successfully!");

            document.getElementById("newCategoryName").value = "";
            document.getElementById("newCategoryType").value = "";

            input_category.innerHTML = '<option value="">Select a category from the dropdown</option>';
            fetch("http://127.0.0.1:8000/categories/?user_id=1")
            .then(response => response.json())
            .then(categories => {
                categories.forEach(category => {
                    const option = document.createElement("option");
                    option.value = category.id;
                    option.textContent = category.name;
                    input_category.appendChild(option);
                });
            });
        });
    }


    //Add transactions
    const addTransactionButton = document.getElementById("addTransactionButton");
    if (addTransactionButton)
    {
        addTransactionButton.addEventListener("click", async () => {
            const user_id = 1;

            const amountInput = document.getElementById("amount").value.trim();
            const description = document.getElementById("description").value.trim();
            const categoryId = document.getElementById("category_dropdown").value;
            const isIncomeRadio = document.querySelector('input[name="agreement"]:checked');

            if (!amountInput || isNaN(amountInput)) {
                alert("Please enter a valid amount.");
                return;
            }
            if (!categoryId) {
                alert("Please select a category.");
                return;
            }
            if (!isIncomeRadio) {
                alert("Please indicate if this is income or an expense.");
                return;
            }

            const payload = {
                amount: parseFloat(amountInput),
                description: description,
                is_income: isIncomeRadio.value === "yes",
                category_id: parseInt(categoryId),
                user_id: user_id
            };

            const url = new URL("http://127.0.0.1:8000/transaction/add_transaction");

            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok)
            {
                alert(data.detail || "Failed to add transaction.");
                return;
            }

            alert("Transaction added successfully!");

            document.getElementById("amount").value = "";
            document.getElementById("description").value = "";
            document.getElementById("category_dropdown").value = "";
            document.querySelectorAll('input[name="agreement"]').forEach(r => r.checked = false);

            if (typeof populateTable === "function") populateTable();
        });
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