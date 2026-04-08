import { useState, useRef } from 'react';
import HistoryPage from './pages/HistoryPage';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Link as LinkIcon,
  Clock,
  Sparkles,
  Users,
  Briefcase,
  DollarSign,
  Video,
  TrendingUp,
  Eye,
  Heart,
  Lock,
  Zap,
  Mail,
  X,
  Plus,
  ArrowRight,
  TrendingDown,
  BadgeCheck,
  Ban,
  FileText,
  MessageSquare,
  Upload,
  ImageIcon,
  Film,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────
type ContentType = 'investment' | 'job' | 'health' | 'news' | 'general';
type InputMode = 'url' | 'video' | 'image';

interface AnalysisResult {
  id: string;
  url: string;
  contentType: ContentType;
  trustScore: number;
  riskLevel: 'low' | 'medium' | 'high';
  riskImpact: {
    financial: 'low' | 'medium' | 'high';
    reputation: 'low' | 'medium' | 'high';
    misinformation: 'low' | 'medium' | 'high';
  };
  detectionMetrics: {
    aiGenerated: number;
    deepfake: number;
    impersonation: number;
    misinformation: number;
    cryptoScam: number;
    romanceScam: number;
    phishing: number;
    identityTheft: number;
  };
  detectedThreats: Array<{
    type: string;
    confidence: number;
    icon: string;
  }>;
  explainableFindings: string[];
  whatToDo: {
    dontDo: string[];
    shouldDo: string[];
    verifyThrough: string[];
  };
  // Extra fields from backend (video/image)
  mediaType?: string;
  confidence?: number;
  framesAnalyzed?: number;
  facesDetected?: number;
  analysisTime?: number;
}

// ─── Backend URL ──────────────────────────────────────────────────────────────
// Change this if you deploy your backend somewhere else
const BACKEND_URL = 'http://localhost:5000';

// ─── Main Component ───────────────────────────────────────────────────────────
export default function App() {
  const [showHistory, setShowHistory]       = useState(false);
  const [link, setLink]                     = useState('');
  const [contentType, setContentType]       = useState<ContentType>('general');
  const [inputMode, setInputMode]           = useState<InputMode>('url');
  const [uploadedFile, setUploadedFile]     = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing]       = useState(false);
  const [results, setResults]               = useState<AnalysisResult[]>([]);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedResult, setSelectedResult] = useState<string | null>(null);
  const [error, setError]                   = useState<string | null>(null);
  const fileInputRef                        = useRef<HTMLInputElement>(null);

  const contentTypes = [
    { value: 'investment', label: 'Investment',   icon: <DollarSign  className="w-5 h-5" /> },
    { value: 'job',        label: 'Job Offer',    icon: <Briefcase   className="w-5 h-5" /> },
    { value: 'health',     label: 'Health Advice',icon: <Heart       className="w-5 h-5" /> },
    { value: 'news',       label: 'News',         icon: <FileText    className="w-5 h-5" /> },
    { value: 'general',    label: 'General',      icon: <MessageSquare className="w-5 h-5" /> },
  ];

  // ── File selection handler ─────────────────────────────────────────────────
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isVideo = file.type.startsWith('video/');
    const isImage = file.type.startsWith('image/');
    if (!isVideo && !isImage) {
      setError('Please upload a video (MP4, MOV, AVI) or image (JPG, PNG, WEBP) file.');
      return;
    }
    setError(null);
    setUploadedFile(file);
    setInputMode(isVideo ? 'video' : 'image');
  };

  // ── Drag and drop ──────────────────────────────────────────────────────────
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    const isVideo = file.type.startsWith('video/');
    const isImage = file.type.startsWith('image/');
    if (!isVideo && !isImage) {
      setError('Please drop a video or image file.');
      return;
    }
    setError(null);
    setUploadedFile(file);
    setInputMode(isVideo ? 'video' : 'image');
  };

  // ── Clear file ─────────────────────────────────────────────────────────────
  const clearFile = () => {
    setUploadedFile(null);
    setInputMode('url');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ── Can analyze check ──────────────────────────────────────────────────────
  const canAnalyze = () => {
    if (isAnalyzing) return false;
    if (inputMode === 'url') return link.trim().length > 0;
    return uploadedFile !== null;
  };

  // ── Main analyze function ──────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!canAnalyze()) return;
    setIsAnalyzing(true);
    setError(null);

    try {
      let response: Response;

      // ── VIDEO UPLOAD ───────────────────────────────────────────────────────
      if (inputMode === 'video' && uploadedFile) {
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('contentType', contentType);
        // NOTE: Do NOT set Content-Type header — browser sets it with boundary automatically
        response = await fetch(`${BACKEND_URL}/analyze/video`, {
          method: 'POST',
          body: formData,
        });

      // ── IMAGE UPLOAD ───────────────────────────────────────────────────────
      } else if (inputMode === 'image' && uploadedFile) {
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('contentType', contentType);
        response = await fetch(`${BACKEND_URL}/analyze/image`, {
          method: 'POST',
          body: formData,
        });

      // ── URL / LINK ─────────────────────────────────────────────────────────
      } else {
        response = await fetch(`${BACKEND_URL}/analyze/url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: link.trim(), contentType }),
        });
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Server error: ${response.status}`);
      }

      const data = await response.json();

      // ── Map backend response → AnalysisResult ─────────────────────────────
      const result: AnalysisResult = {
        id:            Date.now().toString(),
        url:           inputMode === 'url' ? link.trim() : (uploadedFile?.name ?? 'uploaded file'),
        contentType,
        trustScore:    data.trustScore    ?? 50,
        riskLevel:     data.riskLevel     ?? 'medium',
        riskImpact:    data.riskImpact    ?? { financial: 'medium', reputation: 'medium', misinformation: 'medium' },
        detectionMetrics: {
          aiGenerated:   data.detectionMetrics?.aiGenerated   ?? 0,
          deepfake:      data.detectionMetrics?.deepfake       ?? 0,
          impersonation: data.detectionMetrics?.impersonation  ?? 0,
          misinformation:data.detectionMetrics?.misinformation ?? 0,
          cryptoScam:    data.detectionMetrics?.cryptoScam     ?? 0,
          romanceScam:   data.detectionMetrics?.romanceScam    ?? 0,
          phishing:      data.detectionMetrics?.phishing       ?? 0,
          identityTheft: data.detectionMetrics?.identityTheft  ?? 0,
        },
        detectedThreats:     data.detectedThreats     ?? [],
        explainableFindings: data.explainableFindings ?? ['Analysis complete.'],
        whatToDo:            data.whatToDo            ?? { dontDo: [], shouldDo: [], verifyThrough: [] },
        // Video/image extras
        mediaType:      data.mediaType,
        confidence:     data.confidence,
        framesAnalyzed: data.framesAnalyzed,
        facesDetected:  data.facesDetected,
        analysisTime:   data.analysisTime,
      };

      if (comparisonMode) {
        setResults(prev => [...prev, result]);
      } else {
        setResults([result]);
      }
      setSelectedResult(result.id);

    } catch (err: any) {
      console.error('Analysis failed:', err);
      // If backend is not running, fall back to mock data so UI still works
      if (err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) {
        setError('⚠️ Cannot connect to backend (localhost:5000). Make sure Flask is running. Showing demo data instead.');
        useMockFallback();
      } else {
        setError(`Analysis failed: ${err.message}`);
      }
    } finally {
      setIsAnalyzing(false);
      setLink('');
      clearFile();
    }
  };

  // ── Mock fallback (if backend not running) ─────────────────────────────────
  const useMockFallback = () => {
    const score      = Math.floor(Math.random() * 100);
    const trustScore = 100 - score;
    const mockResult: AnalysisResult = {
      id: Date.now().toString(),
      url: link || uploadedFile?.name || 'demo',
      contentType,
      trustScore,
      riskLevel: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
      riskImpact: {
        financial:     contentType === 'investment' || contentType === 'job' ? (score > 70 ? 'high' : score > 40 ? 'medium' : 'low') : 'low',
        reputation:    score > 60 ? 'high' : score > 35 ? 'medium' : 'low',
        misinformation:contentType === 'news' || contentType === 'health' ? (score > 70 ? 'high' : score > 40 ? 'medium' : 'low') : 'medium',
      },
      detectionMetrics: {
        aiGenerated:   Math.floor(Math.random() * 100),
        deepfake:      Math.floor(Math.random() * 100),
        impersonation: Math.floor(Math.random() * 100),
        misinformation:Math.floor(Math.random() * 100),
        cryptoScam:    contentType === 'investment' ? Math.floor(Math.random() * 100) : 0,
        romanceScam:   0,
        phishing:      Math.floor(Math.random() * 100),
        identityTheft: Math.floor(Math.random() * 100),
      },
      detectedThreats: [
        { type: 'Fake Celebrity Endorsement', confidence: 87, icon: 'users' },
        { type: 'AI-Generated Voice Pattern',  confidence: 92, icon: 'sparkles' },
        { type: 'Suspicious Financial Claims', confidence: 76, icon: 'dollar' },
      ],
      explainableFindings: getContextualFindings(contentType, score),
      whatToDo:            getContextualActions(contentType),
    };
    if (comparisonMode) {
      setResults(prev => [...prev, mockResult]);
    } else {
      setResults([mockResult]);
    }
    setSelectedResult(mockResult.id);
  };

  // ── Fallback findings (used when backend is offline) ──────────────────────
  const getContextualFindings = (type: ContentType, score: number): string[] => {
    const findings: Record<ContentType, string[]> = {
      investment: [
        'Unnatural facial movements detected at 0:12 and 0:34',
        'Voice audio shows AI-generated patterns inconsistent with known recordings',
        'Background lighting does not match face lighting (deepfake indicator)',
        'Celebrity likeness used without verified endorsement',
        'Promise of unrealistic returns (500% in 30 days)',
      ],
      job: [
        'Company domain registered less than 2 months ago',
        'LinkedIn profile shows suspicious activity patterns',
        'Job posting requests upfront payment for "training materials"',
        'Salary range significantly above market average for position',
        'Email address does not match official company domain',
      ],
      health: [
        'Claims not verified by medical authorities',
        'AI-generated doctor persona detected',
        'No peer-reviewed research citations provided',
        'Testimonials show pattern matching fake review databases',
        'Urgency tactics used to pressure immediate action',
      ],
      news: [
        'Source not found in verified news databases',
        'Image manipulation detected in 3 out of 5 photos',
        'Claims contradict multiple credible news sources',
        'Website domain mimics legitimate news outlet',
        'No author credentials or editorial board listed',
      ],
      general: [
        'AI-generated content patterns detected',
        'Facial analysis reveals manipulation indicators',
        'Account created recently with suspicious patterns',
        'Content shows characteristics of coordinated inauthentic behavior',
        'Multiple red flags in credibility assessment',
      ],
    };
    return findings[type];
  };

  // ── Fallback actions (used when backend is offline) ────────────────────────
  const getContextualActions = (type: ContentType): AnalysisResult['whatToDo'] => {
    const actions: Record<ContentType, AnalysisResult['whatToDo']> = {
      investment: {
        dontDo: [
          'Do NOT transfer any money or provide banking details',
          'Do NOT share personal identification documents',
          'Do NOT click on investment links or download files',
        ],
        shouldDo: [
          'Verify the celebrity endorsement through their official channels',
          'Check if the company is registered with SC Malaysia (sc.com.my)',
          'Report to Bank Negara Malaysia fraud alert (bnm.gov.my/fraudalert)',
          'Consult with a licensed financial advisor',
        ],
        verifyThrough: [
          'sc.com.my — Securities Commission Malaysia',
          'bnm.gov.my/fraudalert — Bank Negara Malaysia',
          "Celebrity's verified social media accounts only",
        ],
      },
      job: {
        dontDo: [
          'Do NOT pay for training, equipment, or background checks',
          'Do NOT provide NRIC or banking information upfront',
          'Do NOT download files from unofficial sources',
        ],
        shouldDo: [
          'Verify company through SSM Malaysia (ssm.com.my)',
          'Check company reviews on Glassdoor and Indeed',
          'Contact the company directly using their official website number',
          'Report suspicious job postings to the platform',
        ],
        verifyThrough: [
          'ssm.com.my — Companies Commission of Malaysia',
          'LinkedIn company profile (verified badge)',
          'Jobstreet / Indeed company reviews',
        ],
      },
      health: {
        dontDo: [
          'Do NOT purchase unverified medical products',
          'Do NOT stop prescribed medication without consulting your doctor',
          'Do NOT share medical records or insurance information',
        ],
        shouldDo: [
          'Consult with your licensed healthcare provider',
          'Check MOH Malaysia product registration (moh.gov.my)',
          'Verify doctor credentials through Malaysian Medical Council (mmc.gov.my)',
          'Report misleading health claims to FTC / KKM',
        ],
        verifyThrough: [
          'moh.gov.my — Ministry of Health Malaysia',
          'mmc.gov.my — Malaysian Medical Council',
          'WebMD or Mayo Clinic for health information',
        ],
      },
      news: {
        dontDo: [
          'Do NOT share the content without fact-checking',
          'Do NOT make decisions based solely on this source',
          'Do NOT engage with or amplify suspicious content',
        ],
        shouldDo: [
          'Cross-reference with Bernama, The Star, or established outlets',
          'Check sebenarnya.my — Malaysia official fact-checking portal',
          'Look for the story on AP News, Reuters, or BBC',
          'Report misinformation to the social media platform',
        ],
        verifyThrough: [
          'sebenarnya.my — Malaysia official fact checker',
          'Bernama / Reuters / BBC News',
          'FactCheck.org, Snopes.com',
        ],
      },
      general: {
        dontDo: [
          'Do NOT share personal or financial information',
          'Do NOT click on suspicious links',
          'Do NOT forward the content without verification',
        ],
        shouldDo: [
          'Verify through official channels',
          'Report to CyberSecurity Malaysia (cyber999.com)',
          'Use reverse image search to check authenticity',
          'Check trusted sources for similar information',
        ],
        verifyThrough: [
          'cyber999.com — CyberSecurity Malaysia',
          'Official websites and verified social accounts',
          'Fact-checking websites',
        ],
      },
    };
    return actions[type];
  };

  const removeResult = (id: string) => {
    setResults(prev => prev.filter(r => r.id !== id));
    if (selectedResult === id) setSelectedResult(results[0]?.id || null);
  };

  // ── Color helpers (unchanged) ──────────────────────────────────────────────
  const getRiskColor = (level: 'low' | 'medium' | 'high') =>
    level === 'low' ? 'text-green-600' : level === 'medium' ? 'text-yellow-600' : 'text-red-600';

  const getTrustColor = (score: number) =>
    score > 70 ? 'text-green-600' : score > 40 ? 'text-yellow-600' : 'text-red-600';

  const getTrustBg = (score: number) =>
    score > 70
      ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-300'
      : score > 40
      ? 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-300'
      : 'bg-gradient-to-br from-red-50 to-red-100 border-red-300';

  const getMetricColor = (value: number) =>
    value > 70 ? 'text-red-600 bg-red-100' : value > 40 ? 'text-yellow-600 bg-yellow-100' : 'text-green-600 bg-green-100';

  const getProgressColor = (value: number) =>
    value > 70 ? 'bg-red-500' : value > 40 ? 'bg-yellow-500' : 'bg-green-500';

  const getRiskImpactColor = (level: 'low' | 'medium' | 'high') =>
    level === 'low'
      ? 'bg-green-100 text-green-700 border-green-300'
      : level === 'medium'
      ? 'bg-yellow-100 text-yellow-700 border-yellow-300'
      : 'bg-red-100 text-red-700 border-red-300';

  const getThreatIcon = (iconName: string) => {
    switch (iconName) {
      case 'users':    return <Users    className="w-5 h-5" />;
      case 'sparkles': return <Sparkles className="w-5 h-5" />;
      case 'dollar':   return <DollarSign className="w-5 h-5" />;
      case 'video':    return <Video    className="w-5 h-5" />;
      case 'zap':      return <Zap      className="w-5 h-5" />;
      case 'heart':    return <Heart    className="w-5 h-5" />;
      case 'mail':     return <Mail     className="w-5 h-5" />;
      case 'lock':     return <Lock     className="w-5 h-5" />;
      default:         return <AlertTriangle className="w-5 h-5" />;
    }
  };

  const currentResult = results.find(r => r.id === selectedResult);

  // ─── Input mode label helper ───────────────────────────────────────────────
  const getInputModeIcon = () => {
    if (inputMode === 'video') return <Film  className="w-5 h-5 text-pink-400" />;
    if (inputMode === 'image') return <ImageIcon className="w-5 h-5 text-purple-400" />;
    return <LinkIcon className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />;
  };

  // ─── If the user clicked "History", show the history page instead ────────
  // This swaps the entire page content without needing React Router.
  if (showHistory) {
    return <HistoryPage onBack={() => setShowHistory(false)} />;
  }

  // ─── JSX ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">

        {/* ── Header ────────────────────────────────────────────────────────── */}
        <div className="text-center mb-10 pt-8 animate-in fade-in slide-in-from-top duration-700">
          {/* History button — top right corner */}
          <div className="flex justify-end mb-2">
            <button
              onClick={() => setShowHistory(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white transition-all text-sm"
            >
              <Clock className="w-4 h-4" />
              Analysis History
            </button>
          </div>
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-blue-500/20 rounded-2xl backdrop-blur mr-4 hover:scale-110 transition-transform duration-300">
              <Shield className="w-10 h-10 text-blue-400" />
            </div>
            <div className="text-left">
              <h1 className="text-4xl text-white">AI Fraud Intelligence Assistant</h1>
              <p className="text-blue-400 text-xl mt-1">Decision Support System for Social Media Safety</p>
            </div>
          </div>
          <p className="text-gray-300 mt-4 max-w-3xl mx-auto">
            Detect deepfake videos, AI-generated images, and scam social media links —
            then understand the risk and know exactly what to do next
          </p>
        </div>

        {/* ── Error Banner ──────────────────────────────────────────────────── */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/40 rounded-xl flex items-start gap-3 animate-in fade-in duration-300">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-200 text-sm">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ── Input Section ─────────────────────────────────────────────────── */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-8 border border-white/20 animate-in fade-in slide-in-from-bottom duration-700 delay-150">
          
          {/* Top row: label + compare mode */}
          <div className="flex items-center justify-between mb-6">
            <label className="text-white text-lg">What type of content is this?</label>
            <button
              onClick={() => {
                setComparisonMode(!comparisonMode);
                if (!comparisonMode) { setResults([]); setSelectedResult(null); }
              }}
              className={`px-4 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 ${
                comparisonMode ? 'bg-blue-500 text-white hover:bg-blue-600' : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              <Plus className="w-4 h-4" />
              Compare Mode
            </button>
          </div>

          {/* Content type selector */}
          <div className="grid grid-cols-5 gap-3 mb-6">
            {contentTypes.map((type) => (
              <button
                key={type.value}
                onClick={() => setContentType(type.value as ContentType)}
                className={`p-4 rounded-xl border-2 transition-all duration-300 flex flex-col items-center gap-2 hover:scale-105 ${
                  contentType === type.value
                    ? 'bg-blue-500 border-blue-400 text-white shadow-lg'
                    : 'bg-white/5 border-white/20 text-gray-300 hover:bg-white/10'
                }`}
              >
                {type.icon}
                <span className="text-sm font-medium">{type.label}</span>
              </button>
            ))}
          </div>

          {/* ── Input mode tabs ──────────────────────────────────────────────── */}
          <div className="flex gap-2 mb-4">
            {[
              { mode: 'url'   as InputMode, label: 'Paste Link',     icon: <LinkIcon  className="w-4 h-4" /> },
              { mode: 'video' as InputMode, label: 'Upload Video',   icon: <Film      className="w-4 h-4" /> },
              { mode: 'image' as InputMode, label: 'Upload Image',   icon: <ImageIcon className="w-4 h-4" /> },
            ].map(({ mode, label, icon }) => (
              <button
                key={mode}
                onClick={() => { setInputMode(mode); setUploadedFile(null); setLink(''); setError(null); }}
                className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all duration-200 ${
                  inputMode === mode
                    ? 'bg-blue-500 text-white'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                }`}
              >
                {icon}
                {label}
              </button>
            ))}
          </div>

          {/* ── URL input ────────────────────────────────────────────────────── */}
          {inputMode === 'url' && (
            <>
              <label htmlFor="link-input" className="block mb-3 text-white">
                Paste the link you want to analyze
              </label>
              <div className="flex gap-3">
                <div className="flex-1 relative group">
                  <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    id="link-input"
                    type="text"
                    value={link}
                    onChange={(e) => setLink(e.target.value)}
                    placeholder="https://youtube.com/video, linkedin.com/job, or social media post..."
                    className="w-full pl-12 pr-4 py-4 bg-white/90 text-gray-900 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                  />
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={!canAnalyze()}
                  className="px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 duration-200"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center gap-2"><Eye className="w-5 h-5 animate-pulse" />Analyzing...</span>
                  ) : (
                    <span className="flex items-center gap-2">Analyze Risk<ArrowRight className="w-5 h-5" /></span>
                  )}
                </button>
              </div>
            </>
          )}

          {/* ── Video / Image file upload ─────────────────────────────────── */}
          {(inputMode === 'video' || inputMode === 'image') && (
            <div className="space-y-3">
              <label className="block text-white mb-2">
                {inputMode === 'video' ? 'Upload a video to analyze for deepfakes' : 'Upload an image to analyze for AI generation'}
              </label>

              {/* Drop zone */}
              {!uploadedFile ? (
                <div
                  className="border-2 border-dashed border-white/30 rounded-xl p-10 text-center hover:border-blue-400/60 hover:bg-white/5 transition-all duration-300 cursor-pointer"
                  onDrop={handleDrop}
                  onDragOver={(e) => e.preventDefault()}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {inputMode === 'video'
                    ? <Film      className="w-12 h-12 mx-auto mb-3 text-pink-400 opacity-70" />
                    : <ImageIcon className="w-12 h-12 mx-auto mb-3 text-purple-400 opacity-70" />
                  }
                  <p className="text-white mb-1">Drag & drop or click to browse</p>
                  <p className="text-gray-400 text-sm">
                    {inputMode === 'video' ? 'MP4, MOV, AVI, MKV, WEBM — max 100 MB' : 'JPG, PNG, WEBP, GIF — max 20 MB'}
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={inputMode === 'video' ? 'video/*' : 'image/*'}
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                </div>
              ) : (
                /* File selected preview */
                <div className="flex items-center gap-4 p-4 bg-white/10 rounded-xl border border-white/20">
                  {inputMode === 'video'
                    ? <Film      className="w-8 h-8 text-pink-400 flex-shrink-0" />
                    : <ImageIcon className="w-8 h-8 text-purple-400 flex-shrink-0" />
                  }
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{uploadedFile.name}</p>
                    <p className="text-gray-400 text-xs">{(uploadedFile.size / 1024 / 1024).toFixed(1)} MB</p>
                  </div>
                  <button onClick={clearFile} className="p-1 hover:bg-white/10 rounded-lg transition-colors">
                    <X className="w-5 h-5 text-gray-400 hover:text-white" />
                  </button>
                </div>
              )}

              {/* Analyze button for file mode */}
              <button
                onClick={handleAnalyze}
                disabled={!canAnalyze()}
                className="w-full py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl duration-200 flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <><Eye className="w-5 h-5 animate-pulse" />Analyzing {inputMode === 'video' ? 'Video' : 'Image'}...</>
                ) : (
                  <><Upload className="w-5 h-5" />Analyze {inputMode === 'video' ? 'Video' : 'Image'} for Deepfakes<ArrowRight className="w-5 h-5" /></>
                )}
              </button>
            </div>
          )}
        </div>

        {/* ── Comparison View ────────────────────────────────────────────────── */}
        {comparisonMode && results.length > 0 && (
          <div className="mb-8 animate-in fade-in slide-in-from-top duration-500">
            <h3 className="text-white mb-4">Analyzed Items ({results.length})</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.map((result, index) => (
                <div
                  key={result.id}
                  onClick={() => setSelectedResult(result.id)}
                  className={`relative p-4 rounded-xl border-2 transition-all duration-300 text-left hover:scale-105 animate-in fade-in slide-in-from-left cursor-pointer ${
                    selectedResult === result.id
                      ? 'bg-white/20 border-blue-400 shadow-xl'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div
                    onClick={(e) => { e.stopPropagation(); removeResult(result.id); }}
                    className="absolute top-2 right-2 p-1 bg-red-500/80 hover:bg-red-600 rounded-full transition-all hover:scale-110 cursor-pointer"
                  >
                    <X className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`text-3xl ${getTrustColor(result.trustScore)}`}>{result.trustScore}</div>
                    <div>
                      <p className="text-xs text-gray-400">Trust Score</p>
                      <span className={`px-2 py-1 rounded-full text-xs uppercase ${getRiskImpactColor(result.riskLevel)}`}>
                        {result.riskLevel}
                      </span>
                    </div>
                    {result.mediaType && (
                      <span className="ml-auto px-2 py-1 rounded-full text-xs bg-white/10 text-gray-300 uppercase">
                        {result.mediaType}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-300 text-sm truncate">{result.url}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Results Dashboard ──────────────────────────────────────────────── */}
        {currentResult && (
          <div className="space-y-6">

            {/* Trust Score Card */}
            <div className={`rounded-2xl shadow-2xl p-8 border-2 ${getTrustBg(currentResult.trustScore)} animate-in fade-in zoom-in duration-500`}>
              <div className="grid md:grid-cols-3 gap-6 items-center">
                <div className="md:col-span-2">
                  <div className="flex items-center gap-3 mb-4 flex-wrap">
                    <h2 className="text-gray-800 text-2xl">Content Trust Score</h2>
                    <span className={`px-4 py-1 rounded-full text-sm uppercase tracking-wide ${getRiskColor(currentResult.riskLevel)} bg-white animate-in fade-in slide-in-from-right duration-500 delay-200`}>
                      {currentResult.riskLevel === 'high' ? 'Low Trust' : currentResult.riskLevel === 'medium' ? 'Medium Trust' : 'High Trust'}
                    </span>
                    {/* Media type badge */}
                    {currentResult.mediaType && (
                      <span className="px-3 py-1 rounded-full text-xs bg-gray-800 text-gray-200 uppercase tracking-wide">
                        {currentResult.mediaType === 'video' ? '🎬 Video' : currentResult.mediaType === 'image' ? '🖼️ Image' : '🔗 URL'}
                      </span>
                    )}
                  </div>
                  <div className="flex items-baseline gap-4">
                    <div className={`text-7xl ${getTrustColor(currentResult.trustScore)} animate-in zoom-in duration-700 delay-300`}>
                      {currentResult.trustScore}<span className="text-3xl">/100</span>
                    </div>
                    <div className="text-gray-700 animate-in fade-in slide-in-from-bottom duration-500 delay-400">
                      <p className="text-lg font-semibold">
                        {currentResult.trustScore > 70 ? 'Trustworthy Content' :
                         currentResult.trustScore > 40 ? 'Proceed with Caution' :
                         'High Risk — Do Not Trust'}
                      </p>
                      <p className="text-sm text-gray-600">Based on AI intelligence analysis</p>
                      {/* Extra info for video/image */}
                      {currentResult.confidence !== undefined && (
                        <p className="text-sm text-gray-500 mt-1">Detection confidence: {currentResult.confidence}%</p>
                      )}
                      {currentResult.framesAnalyzed !== undefined && (
                        <p className="text-sm text-gray-500">Frames analyzed: {currentResult.framesAnalyzed}</p>
                      )}
                      {currentResult.facesDetected !== undefined && (
                        <p className="text-sm text-gray-500">Faces detected: {currentResult.facesDetected}</p>
                      )}
                      {currentResult.analysisTime !== undefined && (
                        <p className="text-sm text-gray-400">Analysis time: {currentResult.analysisTime}s</p>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex justify-center animate-in zoom-in duration-500 delay-500">
                  <div className={`p-6 rounded-full transition-all duration-300 hover:scale-110 ${
                    currentResult.trustScore > 70 ? 'bg-green-200' :
                    currentResult.trustScore > 40 ? 'bg-yellow-200' : 'bg-red-200'
                  }`}>
                    {currentResult.trustScore > 70
                      ? <BadgeCheck     className="w-20 h-20 text-green-600" />
                      : currentResult.trustScore > 40
                      ? <AlertTriangle  className="w-20 h-20 text-yellow-600" />
                      : <Ban            className="w-20 h-20 text-red-600" />}
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Impact Layer */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-in fade-in slide-in-from-left duration-500">
              <h2 className="mb-6 flex items-center gap-2 text-white text-2xl">
                <TrendingUp className="w-7 h-7 text-orange-400" />
                Potential Risk Impact
              </h2>
              <div className="grid md:grid-cols-3 gap-6">
                {[
                  { label:'Financial Risk',      icon:<DollarSign  className="w-6 h-6 text-red-400"   />, key:'financial'      as const },
                  { label:'Reputation Risk',     icon:<Users       className="w-6 h-6 text-yellow-400"/>, key:'reputation'     as const },
                  { label:'Misinformation Risk', icon:<AlertTriangle className="w-6 h-6 text-purple-400"/>, key:'misinformation' as const },
                ].map(({ label, icon, key }) => (
                  <div key={key} className="bg-white/5 rounded-xl p-6 border border-white/10 hover:scale-105 transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">{icon}<h3 className="text-white">{label}</h3></div>
                      <span className={`px-3 py-1 rounded-full text-sm uppercase font-semibold ${getRiskImpactColor(currentResult.riskImpact[key])} border-2`}>
                        {currentResult.riskImpact[key]}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm">
                      {currentResult.riskImpact[key] === 'high'
                        ? key === 'financial' ? 'Potential for significant financial loss'
                          : key === 'reputation' ? 'Sharing could damage your credibility'
                          : 'Contains false or misleading information'
                        : currentResult.riskImpact[key] === 'medium'
                        ? key === 'financial' ? 'Moderate financial risk present'
                          : key === 'reputation' ? 'Exercise caution before sharing'
                          : 'Some claims require verification'
                        : key === 'financial' ? 'Low financial impact'
                          : key === 'reputation' ? 'Low reputation impact'
                          : 'Low misinformation risk'}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* What Should I Do? */}
            <div className="bg-gradient-to-r from-red-600 via-orange-600 to-red-600 rounded-2xl shadow-2xl p-8 text-white animate-in fade-in zoom-in duration-500">
              <h2 className="mb-6 flex items-center gap-3 text-2xl">
                <Shield className="w-8 h-8" />
                What Should I Do?
              </h2>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <XCircle className="w-6 h-6" />
                    <h3 className="text-lg font-semibold">DON'T</h3>
                  </div>
                  <ul className="space-y-2">
                    {currentResult.whatToDo.dontDo.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Ban className="w-4 h-4 flex-shrink-0 mt-0.5" /><span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="w-6 h-6" />
                    <h3 className="text-lg font-semibold">DO</h3>
                  </div>
                  <ul className="space-y-2">
                    {currentResult.whatToDo.shouldDo.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <ArrowRight className="w-4 h-4 flex-shrink-0 mt-0.5" /><span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <BadgeCheck className="w-6 h-6" />
                    <h3 className="text-lg font-semibold">Verify Through</h3>
                  </div>
                  <ul className="space-y-2">
                    {currentResult.whatToDo.verifyThrough.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" /><span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Explainable Findings */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-in fade-in slide-in-from-bottom duration-500">
              <h2 className="mb-6 flex items-center gap-2 text-white text-2xl">
                <Eye className="w-7 h-7 text-blue-400" />
                Why This Looks Suspicious
              </h2>
              <p className="text-gray-300 mb-4">Here's what our AI detected in plain language:</p>
              <ul className="space-y-3">
                {currentResult.explainableFindings.map((item, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-3 p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 hover:border-blue-400/30 hover:translate-x-2 transition-all duration-300 animate-in fade-in slide-in-from-left"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <span className="w-7 h-7 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-sm font-semibold">
                      {i + 1}
                    </span>
                    <span className="text-gray-200">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Technical Detection Metrics */}
            <details className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:bg-white/10 transition-all cursor-pointer">
              <summary className="text-white text-lg mb-4 cursor-pointer flex items-center gap-2">
                <TrendingDown className="w-6 h-6 text-gray-400" />
                Technical Detection Metrics (Advanced)
              </summary>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                {[
                  { key:'aiGenerated',   label:'AI-Generated',  icon:<Sparkles  className="w-5 h-5" />, color:'purple' },
                  { key:'deepfake',      label:'Deepfake',      icon:<Video     className="w-5 h-5" />, color:'pink'   },
                  { key:'impersonation', label:'Impersonation', icon:<Users     className="w-5 h-5" />, color:'blue'   },
                  { key:'misinformation',label:'Misinformation',icon:<DollarSign className="w-5 h-5"/>, color:'green'  },
                  { key:'phishing',      label:'Phishing',      icon:<Mail      className="w-5 h-5" />, color:'orange' },
                  { key:'identityTheft', label:'Identity Theft',icon:<Lock      className="w-5 h-5" />, color:'indigo' },
                ].map((metric) => {
                  const value = currentResult.detectionMetrics[metric.key as keyof typeof currentResult.detectionMetrics];
                  if (value === 0) return null;
                  return (
                    <div key={metric.key} className="bg-white/5 rounded-xl p-4 border border-white/10 hover:scale-105 transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`text-${metric.color}-400`}>{metric.icon}</div>
                          <h3 className="text-white text-sm">{metric.label}</h3>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getMetricColor(value)}`}>{value}%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-1.5 rounded-full ${getProgressColor(value)} transition-all duration-1000 ease-out`}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </details>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4 justify-center pt-4 animate-in fade-in slide-in-from-bottom duration-500">
              <button
                onClick={() => { if (!comparisonMode) { setResults([]); setSelectedResult(null); } setLink(''); clearFile(); }}
                className="px-6 py-3 bg-white/10 backdrop-blur border-2 border-white/30 text-white rounded-xl hover:bg-white/20 hover:scale-105 active:scale-95 transition-all duration-200"
              >
                Analyze Another
              </button>
              <button
                onClick={() => alert('Downloading detailed intelligence report...')}
                className="px-6 py-3 bg-white text-gray-900 rounded-xl hover:bg-gray-100 hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg"
              >
                Download Full Report
              </button>
              <button
                onClick={() => alert('Thank you for reporting. This helps protect others.')}
                className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg"
              >
                Report to Authorities
              </button>
            </div>
          </div>
        )}

        {/* ── Empty State ────────────────────────────────────────────────────── */}
        {!currentResult && !isAnalyzing && (
          <div className="text-center py-16 animate-in fade-in zoom-in duration-700">
            <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto mb-12">
              {[
                { icon:<Users    className="w-10 h-10 mx-auto mb-3 text-blue-400"  />, title:'Fake Endorsements',  desc:'Celebrity impersonation detection',      delay:0   },
                { icon:<Video    className="w-10 h-10 mx-auto mb-3 text-pink-400"  />, title:'Deepfake Videos',    desc:'AI-manipulated video analysis',           delay:100 },
                { icon:<ImageIcon className="w-10 h-10 mx-auto mb-3 text-purple-400"/>, title:'Fake Images',       desc:'AI-generated photo detection',            delay:200 },
                { icon:<DollarSign className="w-10 h-10 mx-auto mb-3 text-green-400"/>, title:'Financial Fraud',  desc:'Investment scam detection',               delay:300 },
                { icon:<Zap      className="w-10 h-10 mx-auto mb-3 text-yellow-400"/>, title:'Crypto Scams',      desc:'Cryptocurrency fraud alerts',             delay:400 },
                { icon:<Heart    className="w-10 h-10 mx-auto mb-3 text-red-400"   />, title:'Health Misinfo',    desc:'Fake health advice detection',            delay:500 },
                { icon:<Mail     className="w-10 h-10 mx-auto mb-3 text-orange-400"/>, title:'Phishing Links',   desc:'Malicious link identification',           delay:600 },
                { icon:<FileText className="w-10 h-10 mx-auto mb-3 text-indigo-400"/>, title:'Fake News',        desc:'Misinformation detection',                delay:700 },
              ].map((card, i) => (
                <div
                  key={i}
                  className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 hover:scale-110 hover:shadow-2xl hover:border-white/40 transition-all duration-300 cursor-pointer animate-in fade-in zoom-in"
                  style={{ animationDelay: `${card.delay}ms` }}
                >
                  {card.icon}
                  <h3 className="text-white mb-2 font-semibold">{card.title}</h3>
                  <p className="text-gray-400 text-sm">{card.desc}</p>
                </div>
              ))}
            </div>
            <Shield className="w-24 h-24 mx-auto mb-4 text-blue-400/30 animate-pulse" />
            <p className="text-gray-300 text-lg mb-2">Upload a video/image or paste a link to begin analysis</p>
            <p className="text-gray-400 text-sm">We help you make informed decisions about suspicious content</p>
          </div>
        )}

      </div>
    </div>
  );
}
