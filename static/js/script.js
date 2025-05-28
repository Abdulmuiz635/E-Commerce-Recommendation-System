document.addEventListener("DOMContentLoaded", function () {
    const showRecommendationsBtn = document.getElementById("show-recommendations-btn");
    const toast = document.getElementById("toast-popup");
    const recommendationList = document.getElementById("recommendation-list");
    const productId = document.querySelector('input[name="product_id"]').value; // Get the product ID from a hidden input

    if (showRecommendationsBtn && toast && recommendationList) {
      showRecommendationsBtn.addEventListener('click', function() {
        fetch(`/recommendations?product_id=${productId}`) // Send the product ID as a query parameter
          .then(response => response.json())
          .then(data => {
            recommendationList.innerHTML = '';
            if (data && data.length > 0) {
              const topRecommendations = data.slice(0, 5);
              topRecommendations.forEach(product => {
                const productDiv = document.createElement('div');
                productDiv.classList.add('recommended-item');
                productDiv.innerHTML = `
                  <a href="/product/${product.id}">
                    <img src="${product.image_path}" alt="${product.name}" style="max-width: 80px;">
                    <p>${product.name}</p>
                    <p>₦${product.price}</p>
                  </a>
                `;
                recommendationList.appendChild(productDiv);
              });
              toast.classList.add("show");
              setTimeout(() => {
                toast.classList.remove("show");
              }, 5000);
            } else {
              recommendationList.innerHTML = '<p>No recommendations available.</p>';
              toast.classList.add("show");
              setTimeout(() => {
                toast.classList.remove("show");
              }, 3000);
            }
          })
          .catch(error => {
            console.error("Error fetching recommendations:", error);
            recommendationList.innerHTML = '<p>Failed to load recommendations.</p>';
            toast.classList.add("show");
            setTimeout(() => {
              toast.classList.remove("show");
            }, 3000);
          });
      });
    }
  });