import React from 'react';
import { Link } from 'react-router-dom';

export default function PrivacyPage() {
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
          Privacy Policy
        </h1>
        <p className="text-[14px] text-[#64748b]">
          Last updated: June 24, 2026
        </p>
      </header>

      {/* Document Sections */}
      <article className="space-y-8 text-[15px] leading-[1.68] text-[#334155]">
        <p>
          This Privacy Policy explains what information DispatchLens ("we", "us") collects when you use the website and how we use it. By using the service you agree to this policy.
        </p>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            1. Information we collect
          </h2>
          <div className="space-y-3">
            <p>
              <strong className="font-semibold text-[#0f172a]">Account information.</strong> When you create an account we collect your email address and a password (stored as a one-way hash, never in plain text).
            </p>
            <p>
              <strong className="font-semibold text-[#0f172a]">Billing information.</strong> If you subscribe, our payment processor collects the details required to complete your purchase. We do not store full card numbers.
            </p>
            <p>
              <strong className="font-semibold text-[#0f172a]">Usage data.</strong> Basic technical information such as device type, browser, and pages visited, used to keep the service running and improve it.
            </p>
          </div>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            2. How we use information
          </h2>
          <ul className="list-disc list-inside space-y-1.5 pl-1">
            <li>To create and operate your account.</li>
            <li>To process your subscription and provide customer support.</li>
            <li>To detect, prevent, and respond to fraud or abuse.</li>
            <li>To improve the reliability and quality of the service.</li>
          </ul>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            3. Public data
          </h2>
          <p>
            The carrier information presented through the service is sourced from publicly available government records. We do not sell or share your personal account information with advertisers.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            4. Cookies
          </h2>
          <p>
            We use a small number of cookies and similar storage strictly necessary to keep you signed in and to remember your preferences.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            5. Data retention
          </h2>
          <p>
            We keep account data for as long as your account is active. You may request deletion of your account at any time by contacting us, after which we will remove your personal information except where retention is required by law.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            6. Security
          </h2>
          <p>
            We use industry-standard safeguards to protect your information. No method of transmission over the internet is 100% secure, but we work to protect your data using reasonable measures.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            7. Your rights
          </h2>
          <p>
            Depending on your jurisdiction, you may have the right to access, correct, or delete your personal information, and to object to certain processing. Contact us to exercise these rights.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            8. Children
          </h2>
          <p>
            The service is not intended for individuals under 18. We do not knowingly collect information from children.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            9. Changes
          </h2>
          <p>
            We may update this policy from time to time. Material changes will be reflected by updating the date at the top of this page.
          </p>
        </section>
        <section>
          <h2 className="text-[17px] font-bold text-[#0f172a] mb-2.5">
            10. Contact
          </h2>
          <p>
            Questions about this policy can be sent to the support address shown in your account.
          </p>
        </section>
      </article>
    </main>
  );
}
