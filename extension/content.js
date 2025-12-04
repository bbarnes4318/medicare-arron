// Content script to capture form data on buyertrend.org

console.log("📋 Medicare Data Capture active");

// Function to extract form data
function extractFormData() {
  const data = {};

  // Helper to get value by name or selector
  const getValue = (name) => {
    const el =
      document.querySelector(`[name="${name}"]`) ||
      document.querySelector(`[formcontrolname="${name}"]`) ||
      document.getElementById(name);
    return el ? el.value : "";
  };

  // Extract standard fields
  data.first_name = getValue("first_name") || getValue("firstName");
  data.last_name = getValue("last_name") || getValue("lastName");
  data.phone = getValue("phone");
  data.email = getValue("email");
  data.address = getValue("address");
  data.city = getValue("city");
  data.state = getValue("state");
  data.zip_code = getValue("zip_code") || getValue("zip");

  // Capture TrustedForm URL if present in hidden fields or global variables
  const tfEl = document.querySelector('[name="xxTrustedFormCertUrl"]');
  if (tfEl) {
    data.trustedform_cert_url = tfEl.value;
  } else {
    // Try to find it in the DOM if it's not in a standard field
    // Some implementations put it in a global variable or specific container
    // This is a best-effort attempt
  }

  return data;
}

// Listen for submit events on any form
document.addEventListener("submit", function (e) {
  console.log("📝 Form submission detected!");

  // Wait a brief moment to ensure values are finalized (e.g. validation)
  setTimeout(() => {
    const formData = extractFormData();
    console.log("Captured data:", formData);

    // Send to local backend
    fetch("http://localhost:5000/api/save-lead", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("✅ Data sent to local portal:", data);
      })
      .catch((error) => {
        console.error("❌ Error sending data to local portal:", error);
      });
  }, 500);
});

// Also listen for click on submit buttons as a backup (for AJAX forms that might hijack submit)
document.addEventListener("click", function (e) {
  if (
    e.target.matches(
      'button[type="submit"], input[type="submit"], .submit-btn, .btn-submit'
    )
  ) {
    console.log("🖱️ Submit button clicked!");
    // Same logic as above
    setTimeout(() => {
      const formData = extractFormData();
      // Only send if we have at least a phone number or email (avoid empty clicks)
      if (formData.phone || formData.email) {
        fetch("http://localhost:5000/api/save-lead", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        })
          .then((response) => response.json())
          .then((data) => console.log("✅ Data sent:", data))
          .catch((err) => console.error("❌ Error:", err));
      }
    }, 1000);
  }
});
