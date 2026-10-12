import React from 'react';
import { Link } from 'react-router-dom';

export default function RefundPage() {
  return (
    <main className="w-full max-w-[820px] mx-auto px-6 sm:px-8 pt-12 pb-24 flex-1">
      {/* Back Navigation */}
      <div className="mb-8">
        <Link className="inline-flex items-center text-[14px] font-medium text-[#64748b] hover:text-[#0f172a] transition-colors" to="/">
          <svg aria-hidden="true" className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M10 19l-7-7m0 0l7-7m-7 7h18" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path>
          </svg>
          Back home
        </Link>
      </div>

      {/* Page Header */}
      <header className="mb-10">
        <h1 className="text-[34px] sm:text-[38px] font-bold text-[#0f172a] tracking-tight leading-tight mb-2">
          Refund Policy
        </h1>
        <p className="text-[14px] text-[#64748b]">
          Last updated: June 24, 2026
        </p>
      </header>

      {/* Document Sections */}
      <article className="space-y-8 text-[15px] leading-[1.68] text-[#334155]">
        <p>
          This Refund Policy explains the conditions under which payments for the DispatchLens Premium subscription may be refunded. By purchasing a subscription you confirm that you have read and agreed to this policy.
        </p>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            1. No refunds
          </h2>
          <p>
            All payments for the Premium subscription are final and non-refundable. Premium is activated manually after you contact us on WhatsApp at <strong className="font-semibold text-[#0f172a]">+923221945605</strong> and complete the agreed monthly payment. We do not issue refunds for unused time within a billing period, accidental payments, partial-use months, or cancellations made after activation.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            2. Cancellation
          </h2>
          <p>
            You may cancel your subscription at any time from your account. When you cancel, your Premium access remains active until the end of the current billing period; the subscription will not renew thereafter and you will not be charged again.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            3. Free preview before purchase
          </h2>
          <p>
            The Free plan lets you preview the Service and verify that it meets your needs before subscribing. Please make use of it before upgrading — a Premium purchase confirms that you have evaluated the Service and accepted the no-refund policy.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            4. Exceptions required by law
          </h2>
          <p>
            Where local consumer-protection law grants you a mandatory statutory right of withdrawal or refund that cannot be waived, we will honor that right to the extent required by the applicable law. By starting to use Premium features immediately after purchase, you expressly request that the digital service be supplied without delay and, where permitted, acknowledge that this may end any statutory withdrawal right.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            5. Duplicate or fraudulent charges
          </h2>
          <p>
            If you believe you have been charged twice for the same billing period, or that an unauthorized charge has been made on your payment method, contact us promptly with the transaction details and we will investigate.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            6. Chargebacks
          </h2>
          <p>
            Before filing a chargeback with your bank or card issuer, please contact us first so we can attempt to resolve the issue. Filing a chargeback without first contacting us may result in immediate termination of your account.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            7. How to contact us
          </h2>
          <p>
            For any billing question, write to the support address shown in your account.
          </p>
        </section>
      </article>
    </main>
  );
}
