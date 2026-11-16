const cartLink = document.querySelector('[data-cart-link]');
const cartBadge = document.querySelector('[data-cart-count]');
let pendingAddition = Promise.resolve();
let openingCart = false;

window.addEventListener('pageshow', () => {
  openingCart = false;
});

document.addEventListener('submit', (event) => {
  const form = event.target;
  const button = event.submitter;
  if (!form.matches('[data-purchase-actions]') || !button) return;

  event.preventDefault();
  if (openingCart) return;
  if (button.value === 'buy') {
    openingCart = true;
    // The default server response adds the product and redirects to the cart.
    pendingAddition.then(() => form.submit());
    return;
  }

  const data = new FormData(form);
  data.set(button.name, button.value);
  const endpoint = form.getAttribute('action');
  const status = form.querySelector('[data-cart-status]');
  // Wait for the previous response so the next request uses its updated session cookie.
  pendingAddition = pendingAddition.then(async () => {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        body: data,
      });
      if (response.status === 401) {
        const { login_url: loginUrl } = await response.json();
        window.location.assign(loginUrl);
        return;
      }
      if (!response.ok) throw new Error('Cart update failed');
      const { cart_count: count } = await response.json();
      cartBadge.textContent = count;
      cartBadge.classList.toggle('d-none', count === 0);
      cartLink.setAttribute('aria-label', `Giỏ hàng, ${count} sản phẩm`);
      status.classList.remove('text-danger');
      status.classList.add('text-success', 'visually-hidden');
      status.textContent = `Đã thêm vào giỏ hàng. Giỏ hàng có ${count} sản phẩm.`;
    } catch {
      status.classList.remove('text-success', 'visually-hidden');
      status.classList.add('text-danger');
      status.textContent = 'Không thể xác nhận cập nhật. Vui lòng kiểm tra giỏ hàng.';
    }
    status.hidden = false;
  });
});
