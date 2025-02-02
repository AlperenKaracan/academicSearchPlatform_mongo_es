const scrollTopBtn = document.getElementById("scrollTopBtn");
window.addEventListener("scroll", () => {
  if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
    scrollTopBtn.style.display = "block";
  } else {
    scrollTopBtn.style.display = "none";
  }
});

scrollTopBtn.addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    const spinner = document.createElement("div");
    spinner.className = "spinner-border text-primary spinner-overlay";
    spinner.setAttribute("role", "status");
    spinner.innerHTML = '<span class="visually-hidden">Yükleniyor...</span>';
    document.body.appendChild(spinner);
  });
});
const gridViewBtn = document.getElementById("gridViewBtn");
const listViewBtn = document.getElementById("listViewBtn");
const articleGridContainer = document.getElementById("articleGridContainer");
const articleListTable = document.getElementById("articleListTable");

if (gridViewBtn && listViewBtn) {
  gridViewBtn.addEventListener("click", () => {
    articleGridContainer.style.display = "flex";
    articleListTable.style.display = "none";
    gridViewBtn.classList.add("active");
    listViewBtn.classList.remove("active");
  });

  listViewBtn.addEventListener("click", () => {
    articleGridContainer.style.display = "none";
    articleListTable.style.display = "block";
    listViewBtn.classList.add("active");
    gridViewBtn.classList.remove("active");
  });
}
document.querySelectorAll(".view-detail-btn").forEach((button) => {
  button.addEventListener("click", function () {
    const makaleId = this.getAttribute("data-id");
    const modalContent = document.getElementById("articleDetailContent");
    modalContent.innerHTML = '<p class="text-center">Yükleniyor...</p>';
    const detailModal = new bootstrap.Modal(document.getElementById("articleDetailModal"));
    detailModal.show();

    fetch(`/api/makale/${makaleId}`)
      .then((response) => response.json())
      .then((data) => {
        let html = `
          <h3>${data.makale_isim}</h3>
          <p><strong>ID:</strong> ${data.makale_ID}</p>
          <p><strong>Yazar:</strong> ${data.makale_yazar}</p>
          <p><strong>Tür:</strong> ${data.makale_tur}</p>
          <p><strong>Tarih:</strong> ${data.makale_tarih ? data.makale_tarih : '-'}</p>
          <p><strong>Özet:</strong> ${data.makale_ozet}</p>
          <p><strong>Anahtar Kelimeler (Makale):</strong> ${data.makale_anahtarkelimeler}</p>
          <p><strong>Anahtar Kelimeler (Tarayıcı):</strong> ${data.makale_anahtarkelimeler_tarayici}</p>
          <p><strong>DOI:</strong> ${data.makale_doi}</p>
          <hr>
          <h5>Referanslar</h5>
        `;
        if (data.makale_referanslar && data.makale_referanslar.length > 0) {
          html += '<ul class="list-group">';
          data.makale_referanslar.forEach((ref) => {
            html += `<li class="list-group-item">${ref}</li>`;
          });
          html += '</ul>';
        } else {
          html += '<p class="text-muted">Referans bulunamadı.</p>';
        }
        modalContent.innerHTML = html;
      })
      .catch((err) => {
        modalContent.innerHTML = '<p class="text-danger">Detay yüklenirken hata oluştu.</p>';
      });
  });
});
