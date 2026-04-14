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
                return;
            }
            
            localStorage.setItem("isLoggedIn", "true")
            localStorage.setItem("currentUserID", data.user_id)
            localStorage.setItem("welcomeMessage", data.message)
            alert("Login successful! " + localStorage.getItem("welcomeMessage"));
            window.location.href = "index.html";
        });
    }

    //logout logic

    document.getElementById("logout-button").addEventListener("click", logout)

    function logout()
    {
        localStorage.setItem("isLoggedIn", "false")
        localStorage.setItem("currentUserID", "null")
        localStorage.setItem("welcomeMessage", "null")
        alert("You have been logged out.");
        window.location.href = "login.html";   
    }

    //welcome message logic
    const welcome_message = document.getElementById("welcome-message");
    if(welcome_message &&!Object.is(localStorage.getItem("currentUserID"), "null"))
    {
        welcome_message.innerHTML = localStorage.getItem("welcomeMessage");
    }

   /* const input_category = document.getElementById("category_dropdown");
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
    }*/

        //getting categories
const input_category = document.getElementById("category_dropdown");

if (input_category) {
    fetch("http://127.0.0.1:8000/categories/")
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to load categories.");
            }
            return response.json();
        })
        .then(categories => {
            input_category.innerHTML = '<option value="">Select a category from the dropdown</option>';

            categories.forEach(category => {
                const option = document.createElement("option");
                option.value = category.id;
                option.textContent = category.name;
                input_category.appendChild(option);
            });
        })
        .catch(error => {
            console.error("Category dropdown error:", error);
        });
}   
//Add category
    const addCategoryButton = document.getElementById("addCategoryButton");
    if (addCategoryButton)
    {
        addCategoryButton.addEventListener("click", async () => {
            //const user_id = 1;
            const user_id = localStorage.getItem("currentUserID");
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
        const refreshUrl = new URL("http://127.0.0.1:8000/categories/");
        refreshUrl.searchParams.append("user_id", user_id); // ← was hardcoded to 1
        fetch(refreshUrl)
            .then(r => r.json())
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
    if (addTransactionButton) {
        addTransactionButton.addEventListener("click", async () => {
            const user_id = localStorage.getItem("currentUserID"); // ← make sure this is here

            const amountInput = document.getElementById("amount").value.trim();
            const description = document.getElementById("description").value.trim();
            const categoryId = document.getElementById("category_dropdown").value;
            const isIncomeRadio = document.querySelector('input[name="agreement"]:checked');

            if (!amountInput || isNaN(amountInput)) { alert("Please enter a valid amount."); return; }
            if (!categoryId) { alert("Please select a category."); return; }
            if (!isIncomeRadio) { alert("Please indicate if this is income or an expense."); return; }

            const payload = {
                amount: parseFloat(amountInput),
                description: description,
                is_income: isIncomeRadio.value === "yes",
                category_id: parseInt(categoryId),
                user_id: parseInt(user_id)  // ← add this
            };

            const res = await fetch("http://127.0.0.1:8000/transaction/add_transaction", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                // ← This is the [object Object] fix
                const errorMsg = typeof data.detail === "string"
                    ? data.detail
                    : JSON.stringify(data.detail);
                alert(errorMsg || "Failed to add transaction.");
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

    // Populate delete dropdown
async function populateDeleteDropdown() {
    const dropdown = document.getElementById("delete_transaction_dropdown");
    if (!dropdown) return;

    const user_id = localStorage.getItem("currentUserID");
    if (!user_id || user_id === "null") return;

    try {
        const res = await fetch(`http://127.0.0.1:8000/transaction/${user_id}`);
        if (!res.ok) return;

        const transactions = await res.json();

        dropdown.innerHTML = '<option value="">Select a transaction to delete</option>';

        transactions.forEach(transaction => {
            const option = document.createElement("option");
            option.value = transaction.id;

            // Show enough info to identify the transaction
            const sign = transaction.is_income ? "+" : "-";
            const amount = transaction.amount.toLocaleString("en-US", {
                style: "currency",
                currency: "USD"
            });
            const date = new Date(transaction.date).toLocaleDateString();
            const desc = transaction.description || "No description";

            option.textContent = `${date} | ${desc} | ${sign}${amount}`;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error("Failed to load transactions for delete dropdown:", error);
    }
}

// Delete transaction button
const deleteTransactionButton = document.getElementById("deleteTransactionButton");
if (deleteTransactionButton) {
    deleteTransactionButton.addEventListener("click", async () => {
        const user_id = localStorage.getItem("currentUserID");
        const dropdown = document.getElementById("delete_transaction_dropdown");
        const transaction_id = dropdown.value;

        if (!transaction_id) {
            alert("Please select a transaction to delete.");
            return;
        }

        if (!confirm("Are you sure you want to delete this transaction?")) return;

        const res = await fetch(
            `http://127.0.0.1:8000/transaction/${user_id}/${transaction_id}`,
            { method: "DELETE" }
        );

        const data = await res.json();

        if (!res.ok) {
            const errorMsg = typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(data.detail);
            alert(errorMsg || "Failed to delete transaction.");
            return;
        }

        alert("Transaction deleted!");
        populateDeleteDropdown(); // refresh the delete dropdown
        populateTable();          // refresh the main table
    });
}


    //auto-populating table that pulls and displays a user's transactions
    async function populateTable()
    {
        const tableBody = document.getElementById("table-body");
        tableBody.innerHTML = "";
        
        try 
        {
            const user_id = localStorage.getItem("currentUserID");

            if(!user_id || user_id === "null")
            {
                throw new Error("User not logged in or user info missing.");
            }
                
            const balanceurl = new URL("http://127.0.0.1:8000/transaction/balance");
            const transactionurl = new URL(`http://127.0.0.1:8000/transaction/${user_id}`);
            //-const categoryurl = new URL("http://127.0.0.1:8000/categories");
            
            balanceurl.searchParams.append("user_id", user_id);

            const balres = await fetch(balanceurl, { method: "GET" });
            const transres = await fetch(transactionurl, { method: "GET" });
            //const catres = await fetch(categoryurl, { method: "GET" });

            if (!balres.ok || !transres.ok) 
            {
                throw new Error("Transaction or balance data currently unavailable.");
            }

            const balance = await balres.json();
            const transactions = await transres.json();
            //const categories = await catres.json();

            // const categoryMap = {};
            //     categories.forEach(cat => {
            //     categoryMap[cat.id] = cat.name;
            // });

            const balanceTotal = document.getElementById("budget-total");
            balanceTotal.innerHTML = `Your current balance is $${balance.balance}.`;
            balanceTotal.style.color = (balance.balance > 0) ? "green" : "red";

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
        catch (error)
        {
            displayTableError(tableBody, error.message);
        }
    }
<<<<<<< HEAD
    populateTable();
});

// Group expenses by category
const categoryTotals = {};

transactions.forEach(transaction => {
    if (!transaction.is_income) { // only expenses
        const category = transaction.category_id;

        if (!categoryTotals[category]) {
            categoryTotals[category] = 0;
        }

        categoryTotals[category] += transaction.amount;
    }
    
});

// Prepare data for chart
const labels = Object.keys(categoryTotals);
const data = Object.values(categoryTotals);

async function populateTable()
{
    const tableBody = document.getElementById("table-body");
    tableBody.innerHTML = "";

    const user_id = "1";

    const balanceurl = new URL("http://127.0.0.1:8000/transaction/balance");
    const transactionurl = new URL(`http://127.0.0.1:8000/transaction/${user_id}`);

    balanceurl.searchParams.append("user_id", user_id);

    const balres = await fetch(balanceurl);
    const transres = await fetch(transactionurl);

    if (!balres.ok || !transres.ok) 
    {
        const err = await balres.json();
        console.error(err);
        return;
    }

    const balance = await balres.json();
    const transactions = await transres.json();

    // ===== TABLE =====
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
    });

    // ===== PIE CHART =====
    const categoryTotals = {};

transactions.forEach(transaction => {
    if (!transaction.is_income) { // only expenses
        const cat = transaction.category_id;

        if (!categoryTotals[cat]) {
            categoryTotals[cat] = 0;
        }

        categoryTotals[cat] += transaction.amount;
    }
});
const labels = Object.keys(categoryTotals);
const data = Object.values(categoryTotals);

const ctx = document.getElementById("expenseChart").getContext("2d");

new Chart(ctx, {
    type: "pie",
    data: {
        labels: labels,
        datasets: [{
            label: "Expenses by Category",
            data: data,
            backgroundColor: [
                "#FF6384",
                "#36A2EB",
                "#FFCE56",
                "#4BC0C0",
                "#9966FF",
                "#FF9F40"
            ]
        }]
    },
    options: {
        responsive: true
    }
});

}

populateTable();// Create pie chart
const ctx = document.getElementById("expenseChart").getContext("2d");



function openPopup() {
    document.getElementById("popup").style.display = "block";
}

function closePopup() {
    document.getElementById("popup").style.display = "none";
}

window.onclick = function(event) {
    let popup = document.getElementById("popup");
    if (event.target === popup) {
        popup.style.display = "none";
    }
}
=======

    function displayTableError(tableBody, message)
    {
        const row = tableBody.insertRow();
        const cell = row.insertCell(0);
        cell.colSpan = 5;
        cell.innerHTML = message;
        cell.style.textAlign = "center";
        cell.style.color = "red";
    }

    populateTable(); //on index.html load
    populateDeleteDropdown();
});
>>>>>>> origin/main
