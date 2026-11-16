
const API = "http://127.0.0.1:8000";

let token = sessionStorage.getItem("token");
let role = sessionStorage.getItem("role");

const statusBox = document.querySelector("#status");

function message(text) {
    statusBox.textContent = text;
}

function headers(json = false) {
    const h = {};

    if (json) h["Content-Type"] = "application/json";
    if (token) h.Authorization = `Bearer ${token}`;

    return h;
}

async function request(path, options = {}) {
    const response = await fetch(API + path, options);

    if (response.status === 204) return null;

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}

function showRole() {
    document.querySelector("#admin-panel").hidden = role !== "admin";
}

showRole();


document.querySelector("#register-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());

    if (!payload.admin_code) delete payload.admin_code;

    try {
        const result = await request("/auth/register", {
            method: "POST",
            headers: headers(true),
            body: JSON.stringify(payload)
        });

        message(`Account created with role: ${result.role}. Now log in.`);
        event.currentTarget.reset();

    } catch (error) {
        message(error.message);
    }
});


document.querySelector("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const body = new URLSearchParams();

    body.set("username", form.get("email"));
    body.set("password", form.get("password"));

    try {
        const result = await request("/auth/login", {
            method: "POST",
            body
        });

        token = result.access_token;
        role = result.role;

        sessionStorage.setItem("token", token);
        sessionStorage.setItem("role", role);

        showRole();
        message(`Logged in as ${role}.`);

        await loadStudents();

    } catch (error) {
        message(error.message);
    }
});

async function loadStudents() {
    try {
        const students = await request("/students", {
            headers: headers()
        });

        const list = document.querySelector("#student-list");
        list.replaceChildren();

        for (const student of students) {
            const item = document.createElement("li");
            item.textContent = `${student.name} — ${student.email} — ${student.course}`;
            list.append(item);
        }

        message(`${students.length} student record(s) loaded.`);

    } catch (error) {
        message(error.message);
    }
}

document.querySelector("#student-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = Object.fromEntries(
        new FormData(event.currentTarget).entries()
    );

    try {
        await request("/students", {
            method: "POST",
            headers: headers(true),
            body: JSON.stringify(payload)
        });

        event.currentTarget.reset();
        message("Student added.");
        await loadStudents();

    } catch (error) {
        message(error.message);
    }
});

document.querySelector("#refresh").addEventListener("click", loadStudents);

document.querySelector("#logout").addEventListener("click", () => {
    token = null;
    role = null;

    sessionStorage.clear();

    showRole();

    document.querySelector("#student-list").replaceChildren();

    message("Logged out.");
});