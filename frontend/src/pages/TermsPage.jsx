import React from 'react';
import { Link } from 'react-router-dom';

export default function TermsPage() {
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
          Terms of Service
        </h1>
        <p className="text-[14px] text-[#64748b]">
          Last updated: June 24, 2026
        </p>
      </header>

      {/* Document Sections */}
      <article className="space-y-8 text-[15px] leading-[1.68] text-[#334155]">
        <p>
          These Terms of Service ("Terms") govern your access to and use of DispatchLens (the "Service"). By creating an account or using the Service you agree to these Terms.
        </p>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            1. Eligibility
          </h2>
          <p>
            You must be at least 18 years old and able to enter into a binding contract to use the Service.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            2. Accounts
          </h2>
          <p>
            You are responsible for the activity that happens under your account and for keeping your credentials confidential. Notify us promptly of any unauthorized use.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            3. Subscription and payment
          </h2>
          <p>
            Premium access is billed as a recurring monthly subscription at the price displayed on the pricing page. Your subscription renews automatically each billing period until you cancel.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            4. Acceptable use
          </h2>
          <ul className="list-disc list-inside space-y-1.5 pl-1">
            <li>Do not attempt to bypass usage limits or security controls.</li>
            <li>Do not scrape, resell, or redistribute exported data in bulk to third parties as a competing product.</li>
            <li>Do not use the Service to send unsolicited messages in violation of applicable laws (including anti-spam laws).</li>
            <li>Do not use the Service for unlawful purposes.</li>
          </ul>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            5. Data and content
          </h2>
          <p>
            The Service surfaces information sourced from publicly available government records. The Service is provided "as is" with no warranty regarding the completeness, accuracy, or timeliness of that information. You are responsible for how you use it.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            6. Intellectual property
          </h2>
          <p>
            The Service, including its design, branding, and software, is owned by us and protected by intellectual-property laws. We grant you a limited, non-exclusive, non-transferable right to use the Service for its intended purpose.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            7. Suspension and termination
          </h2>
          <p>
            We may suspend or terminate your access if you violate these Terms or use the Service in a way that risks harm to us or others. You may stop using the Service at any time by cancelling your subscription.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            8. Disclaimers
          </h2>
          <p>
            The Service is provided on an "as is" and "as available" basis without warranties of any kind, whether express or implied, including but not limited to merchantability, fitness for a particular purpose, and non-infringement.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            9. Limitation of liability
          </h2>
          <p>
            To the maximum extent permitted by law, we will not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenue, whether incurred directly or indirectly.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            10. Changes to the Terms
          </h2>
          <p>
            We may update these Terms from time to time. We will indicate material changes by updating the date at the top of this page. Continued use of the Service after changes take effect constitutes acceptance.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            11. Governing law
          </h2>
          <p>
            These Terms are governed by the laws applicable in the jurisdiction where the Service operator is established, without regard to conflict-of-law principles.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            12. Contact
          </h2>
          <p>
            Questions about these Terms can be sent to the support address shown in your account.
          </p>
        </section>
      </article>
    </main>
  );
}
