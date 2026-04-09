import { useState } from 'react';
import { X, AlertTriangle, Send, CheckCircle } from 'lucide-react';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisData: {
    url: string;
    contentType: string;
    trustScore: number;
    riskLevel: string;
    uploadedFiles?: Array<{ file: File; type: 'image' | 'video' }>;
  };
}

export function ReportModal({ isOpen, onClose, analysisData }: ReportModalProps) {
  const [reportDetails, setReportDetails] = useState({
    reporterName: '',
    reporterEmail: '',
    incidentDate: '',
    additionalInfo: '',
    affectedFinancially: false,
    lostAmount: '',
    reportToAgencies: [] as string[],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const agencies = [
    { id: 'fbi', label: 'FBI Internet Crime Complaint Center (IC3)', country: 'USA' },
    { id: 'ftc', label: 'Federal Trade Commission (FTC)', country: 'USA' },
    { id: 'sec', label: 'Securities and Exchange Commission (SEC)', country: 'USA' },
    { id: 'actionfraud', label: 'Action Fraud', country: 'UK' },
    { id: 'europol', label: 'Europol', country: 'EU' },
    { id: 'local', label: 'Local Police Department', country: 'Any' },
  ];

  const handleAgencyToggle = (agencyId: string) => {
    setReportDetails(prev => ({
      ...prev,
      reportToAgencies: prev.reportToAgencies.includes(agencyId)
        ? prev.reportToAgencies.filter(id => id !== agencyId)
        : [...prev.reportToAgencies, agencyId]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate backend API call
    const reportPayload = {
      ...reportDetails,
      analysisData: {
        url: analysisData.url,
        contentType: analysisData.contentType,
        trustScore: analysisData.trustScore,
        riskLevel: analysisData.riskLevel,
      },
      uploadedFiles: analysisData.uploadedFiles?.map(item => ({
        name: item.file.name,
        size: item.file.size,
        type: item.type,
      })),
      timestamp: new Date().toISOString(),
    };

    // Simulate API call
    console.log('Submitting report to backend:', reportPayload);

    // In production, this would be:
    // await fetch('/api/report-to-authorities', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(reportPayload)
    // });

    setTimeout(() => {
      setIsSubmitting(false);
      setIsSuccess(true);
    }, 2000);
  };

  if (!isOpen) return null;

  if (isSuccess) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-2xl p-8 max-w-md w-full text-center animate-in zoom-in duration-300">
          <CheckCircle className="w-16 h-16 text-white mx-auto mb-4" />
          <h2 className="text-2xl text-white mb-3">Report Submitted Successfully</h2>
          <p className="text-green-100 mb-6">
            Your report has been submitted to the selected authorities. Reference ID: <strong>#{Math.random().toString(36).substr(2, 9).toUpperCase()}</strong>
          </p>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-white text-green-700 rounded-lg hover:bg-gray-100 transition-all"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl max-w-3xl w-full my-8 border border-white/20">
        <div className="flex items-center justify-between p-6 border-b border-white/20">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-red-400" />
            <h2 className="text-2xl text-white">Report to Authorities</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-all"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Analysis Summary */}
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
            <h3 className="text-white mb-2">Content Being Reported</h3>
            <p className="text-gray-300 text-sm mb-2 break-all">{analysisData.url}</p>
            <div className="flex gap-3 text-sm">
              <span className="px-3 py-1 bg-red-500/20 text-red-300 rounded-full">
                Trust Score: {analysisData.trustScore}/100
              </span>
              <span className="px-3 py-1 bg-orange-500/20 text-orange-300 rounded-full">
                Risk: {analysisData.riskLevel}
              </span>
            </div>
          </div>

          {/* Reporter Information */}
          <div className="space-y-4">
            <h3 className="text-white">Your Information</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-300 mb-2 text-sm">Your Name</label>
                <input
                  type="text"
                  required
                  value={reportDetails.reporterName}
                  onChange={(e) => setReportDetails(prev => ({ ...prev, reporterName: e.target.value }))}
                  className="w-full px-4 py-2 bg-white/10 text-white border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-gray-300 mb-2 text-sm">Email Address</label>
                <input
                  type="email"
                  required
                  value={reportDetails.reporterEmail}
                  onChange={(e) => setReportDetails(prev => ({ ...prev, reporterEmail: e.target.value }))}
                  className="w-full px-4 py-2 bg-white/10 text-white border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="john@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-gray-300 mb-2 text-sm">When did you encounter this?</label>
              <input
                type="date"
                required
                value={reportDetails.incidentDate}
                onChange={(e) => setReportDetails(prev => ({ ...prev, incidentDate: e.target.value }))}
                className="w-full px-4 py-2 bg-white/10 text-white border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Financial Impact */}
          <div className="bg-white/5 rounded-xl p-4 border border-white/20">
            <label className="flex items-center gap-2 text-white mb-3">
              <input
                type="checkbox"
                checked={reportDetails.affectedFinancially}
                onChange={(e) => setReportDetails(prev => ({ ...prev, affectedFinancially: e.target.checked }))}
                className="w-4 h-4 rounded"
              />
              I was affected financially by this scam
            </label>
            {reportDetails.affectedFinancially && (
              <input
                type="number"
                value={reportDetails.lostAmount}
                onChange={(e) => setReportDetails(prev => ({ ...prev, lostAmount: e.target.value }))}
                className="w-full px-4 py-2 bg-white/10 text-white border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Estimated amount lost ($)"
              />
            )}
          </div>

          {/* Additional Information */}
          <div>
            <label className="block text-gray-300 mb-2 text-sm">Additional Details</label>
            <textarea
              value={reportDetails.additionalInfo}
              onChange={(e) => setReportDetails(prev => ({ ...prev, additionalInfo: e.target.value }))}
              className="w-full px-4 py-2 bg-white/10 text-white border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32 resize-none"
              placeholder="Provide any additional information that might help authorities..."
            />
          </div>

          {/* Select Authorities */}
          <div>
            <h3 className="text-white mb-3">Select Authorities to Report To</h3>
            <div className="space-y-2">
              {agencies.map(agency => (
                <label
                  key={agency.id}
                  className="flex items-start gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-lg border border-white/20 cursor-pointer transition-all"
                >
                  <input
                    type="checkbox"
                    checked={reportDetails.reportToAgencies.includes(agency.id)}
                    onChange={() => handleAgencyToggle(agency.id)}
                    className="mt-1 w-4 h-4 rounded"
                  />
                  <div className="flex-1">
                    <p className="text-white text-sm">{agency.label}</p>
                    <p className="text-gray-400 text-xs">{agency.country}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || reportDetails.reportToAgencies.length === 0}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 disabled:from-gray-500 disabled:to-gray-600 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Submit Report
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
