document.addEventListener("DOMContentLoaded", () => {
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = "0.6";
        }, 4000);
    });

    const deliveryType = document.getElementById("delivery_type");
    const addressBox = document.getElementById("address_box");

    const paymentMethod = document.getElementById("payment_method");
    const cashBox = document.getElementById("cash_box");

    function toggleAddress() {
        if (!deliveryType || !addressBox) return;
        addressBox.classList.toggle("hidden", deliveryType.value !== "entrega");
    }

    function toggleCash() {
        if (!paymentMethod || !cashBox) return;
        cashBox.classList.toggle("hidden", paymentMethod.value !== "Dinheiro");
    }

    if (deliveryType) {
        deliveryType.addEventListener("change", toggleAddress);
        toggleAddress();
    }

    if (paymentMethod) {
        paymentMethod.addEventListener("change", toggleCash);
        toggleCash();
    }

    const menuToggle = document.querySelector(".menu-toggle");
    const mainNav = document.querySelector(".main-nav");

    if (menuToggle && mainNav) {
        menuToggle.addEventListener("click", () => {
            menuToggle.classList.toggle("active");
            mainNav.classList.toggle("active");
        });

        mainNav.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                menuToggle.classList.remove("active");
                mainNav.classList.remove("active");
            });
        });
    }
});


// Aviso visual simples para pedidos recebidos no painel administrativo
(() => {
    const received = document.querySelectorAll('.status-recebido');
    if (!received.length) return;
    document.title = `🔔 ${document.title}`;
})();


// V13 - Animações ao rolar a página inspiradas no pacote animacoes-main
(() => {
    const animatedItems = document.querySelectorAll(
        ".section-head, .category-title, .card, .panel, .form-card, .order-form, .stat, .table-wrap, .cart-item, .checkout-product"
    );

    if (!animatedItems.length) return;

    if (!("IntersectionObserver" in window)) {
        animatedItems.forEach((item) => item.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.14, rootMargin: "0px 0px -40px 0px" });

    animatedItems.forEach((item, index) => {
        item.style.transitionDelay = `${Math.min(index * 45, 360)}ms`;
        observer.observe(item);
    });
})();

// Telefone do cliente: permite apenas o celular da região 35, com 9 dígitos.
(() => {
    const phoneInputs = document.querySelectorAll('input[name="customer_phone"]');
    phoneInputs.forEach((input) => {
        input.addEventListener('input', () => {
            input.value = input.value.replace(/\D/g, '').slice(0, 9);
        });
    });
})();


// V15 - Microinteração: destaca o carrinho quando um item é adicionado
(() => {
    const successFlash = Array.from(document.querySelectorAll('.flash.success')).find(el =>
        (el.textContent || '').toLowerCase().includes('adicionado ao carrinho')
    );
    if (!successFlash) return;
    const cartLinks = document.querySelectorAll('a[href="/carrinho"]');
    cartLinks.forEach(link => {
        link.classList.add('cart-bounce');
        setTimeout(() => link.classList.remove('cart-bounce'), 1200);
    });
})();


// V16 - Busca rápida no cardápio
(() => {
    const search = document.getElementById('menu_search');
    const products = document.querySelectorAll('.menu-product');
    if (!search || !products.length) return;
    search.addEventListener('input', () => {
        const term = search.value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
        products.forEach((product) => {
            const name = (product.dataset.name || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
            product.classList.toggle('is-hidden', term && !name.includes(term));
        });
    });
})();

// V16 - Botões rápidos de observação no checkout
(() => {
    const notes = document.getElementById('notes');
    const buttons = document.querySelectorAll('.quick-notes button[data-note]');
    if (!notes || !buttons.length) return;
    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            const note = button.dataset.note;
            const current = notes.value.trim();
            if (current.toLowerCase().includes(note.toLowerCase())) return;
            notes.value = current ? `${current}; ${note}` : note;
            notes.focus();
        });
    });
})();

// V16 - Parallax suave do vídeo principal
(() => {
    const video = document.querySelector('.hero-video');
    if (!video) return;
    const update = () => {
        const y = Math.min(window.scrollY * 0.06, 34);
        video.style.transform = `scale(1.06) translateY(${y}px)`;
    };
    window.addEventListener('scroll', update, { passive: true });
    update();
})();


// PWA: permite instalar o site no celular como aplicativo.
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js').catch(() => null);
    });
}

// Atualiza automaticamente o painel da cozinha a cada 45 segundos.
if (window.location.pathname.includes('/admin/cozinha')) {
    setTimeout(() => window.location.reload(), 45000);
}


// V17 - Ticket flutuante: corrigido para aparecer novamente.
// Antes ele podia ficar oculto para sempre por causa do localStorage.
(() => {
    const ticket = document.querySelector('.floating-discount-ticket');
    if (!ticket) return;

    // Remove o bloqueio antigo salvo no navegador, garantindo que o cupom volte a aparecer.
    localStorage.removeItem('chapa_ticket_hidden');

    const close = ticket.querySelector('.floating-ticket-close');
    const link = ticket.querySelector('.floating-ticket-link');
    const coupon = (ticket.dataset.ticketCoupon || 'CHAPA10').trim().toUpperCase();

    ticket.style.display = 'block';

    // Ao fechar, esconde apenas enquanto a aba atual estiver aberta.
    if (sessionStorage.getItem('chapa_ticket_hidden_session') === '1') {
        ticket.style.display = 'none';
    }

    if (close) {
        close.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            ticket.style.display = 'none';
            sessionStorage.setItem('chapa_ticket_hidden_session', '1');
        });
    }

    if (link) {
        link.addEventListener('click', () => {
            localStorage.setItem('chapa_ticket_coupon', coupon);
        });
    }

    const couponInput = document.getElementById('coupon_code');
    const savedCoupon = localStorage.getItem('chapa_ticket_coupon');
    if (couponInput && savedCoupon && !couponInput.value) {
        couponInput.value = savedCoupon;
    }
})();
