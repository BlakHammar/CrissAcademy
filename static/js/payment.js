// This file is for handling Stripe payments
document.addEventListener('DOMContentLoaded', function() {
    const stripe = Stripe('YOUR_STRIPE_PUBLIC_KEY'); // Replace with your actual public key

    const paymentForm = document.querySelector('#payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Create a payment intent on the server and get the client secret
            fetch('/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    course_id: paymentForm.dataset.courseId
                })
            })
            .then(response => response.json())
            .then(data => {
                stripe.confirmCardPayment(data.clientSecret, {
                    payment_method: {
                        card: elements.getElement('card'),
                        billing_details: {
                            name: document.querySelector('#name').value
                        }
                    }
                }).then(function(result) {
                    if (result.error) {
                        // Show error to your customer
                        console.error(result.error.message);
                    } else {
                        // The payment succeeded!
                        window.location.href = '/payment-success/' + paymentForm.dataset.courseId;
                    }
                });
            });
        });
    }
});
