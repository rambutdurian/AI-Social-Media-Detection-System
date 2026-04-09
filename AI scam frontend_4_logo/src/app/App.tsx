import { useState } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Link as LinkIcon,
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
  Upload
} from 'lucide-react';
import { FileUploader } from './components/FileUploader';
import { ReportModal } from './components/ReportModal';
import logo from 'figma:asset/fbc2bf6f2f13afea53df0b6af8a561ce0305795a.png';

type ContentType = 'investment' | 'job' | 'health' | 'news' | 'general';

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
  uploadedFiles?: Array<{ file: File; type: 'image' | 'video' }>;
}

export default function App() {
  const [link, setLink] = useState('');
  const [contentType, setContentType] = useState<ContentType>('general');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedResult, setSelectedResult] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ file: File; type: 'image' | 'video' }>>([]);
  const [showUploader, setShowUploader] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const contentTypes = [
    { value: 'investment', label: 'Financial/Investment', icon: <DollarSign className="w-5 h-5" /> },
    { value: 'news', label: 'News/Misinformation', icon: <FileText className="w-5 h-5" /> },
    { value: 'job', label: 'Celebrity/CEO Video', icon: <Users className="w-5 h-5" /> },
    { value: 'health', label: 'Political Figure', icon: <BadgeCheck className="w-5 h-5" /> },
    { value: 'general', label: 'General Content', icon: <MessageSquare className="w-5 h-5" /> },
  ];

  const handleFileSelect = (file: File, type: 'image' | 'video') => {
    setUploadedFiles(prev => [...prev, { file, type }]);
  };

  const handleUrlFromUploader = (url: string) => {
    setLink(url);
  };

  const handleAnalyze = () => {
    if (!link.trim()) return;

    setIsAnalyzing(true);

    // Simulate AI analysis with context-aware mock data
    // In production, this would send to backend API with uploaded files
    setTimeout(() => {
      const score = Math.floor(Math.random() * 100);
      const trustScore = 100 - score; // Invert for trust score

      const mockResult: AnalysisResult = {
        id: Date.now().toString(),
        url: link,
        contentType,
        trustScore,
        riskLevel: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
        uploadedFiles: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
        riskImpact: {
          financial: contentType === 'investment' || contentType === 'job' ? (score > 70 ? 'high' : score > 40 ? 'medium' : 'low') : 'low',
          reputation: score > 60 ? 'high' : score > 35 ? 'medium' : 'low',
          misinformation: contentType === 'news' || contentType === 'health' ? (score > 70 ? 'high' : score > 40 ? 'medium' : 'low') : 'medium',
        },
        detectionMetrics: {
          aiGenerated: Math.floor(Math.random() * 100),
          deepfake: Math.floor(Math.random() * 100),
          impersonation: Math.floor(Math.random() * 100),
          misinformation: Math.floor(Math.random() * 100),
          cryptoScam: contentType === 'investment' ? Math.floor(Math.random() * 100) : 0,
          romanceScam: 0,
          phishing: Math.floor(Math.random() * 100),
          identityTheft: Math.floor(Math.random() * 100),
        },
        detectedThreats: [
          { type: 'Fake Celebrity Endorsement', confidence: 87, icon: 'users' },
          { type: 'AI-Generated Voice Pattern', confidence: 92, icon: 'sparkles' },
          { type: 'Suspicious Financial Claims', confidence: 76, icon: 'dollar' },
        ],
        explainableFindings: getContextualFindings(contentType, score),
        whatToDo: getContextualActions(contentType, score),
      };

      if (comparisonMode) {
        setResults(prev => [...prev, mockResult]);
        setSelectedResult(mockResult.id);
      } else {
        setResults([mockResult]);
        setSelectedResult(mockResult.id);
      }

      setIsAnalyzing(false);
      setLink('');
      setUploadedFiles([]);
      setShowUploader(false);
    }, 2000);
  };

  const getContextualFindings = (type: ContentType, score: number): string[] => {
    const findings: { [key in ContentType]: string[] } = {
      investment: [
        'Unnatural facial movements detected at 0:12 and 0:34 seconds',
        'Voice pattern analysis shows AI-generated speech inconsistencies',
        'Background lighting does not match face lighting (deepfake indicator)',
        'Promises unrealistic returns of 500% within 30 days',
        'Celebrity likeness used without verified endorsement from official sources',
      ],
      job: [
        'Face morphing detected - likely AI-generated celebrity impersonation',
        'Voice does not match verified recordings of this public figure',
        'Video metadata shows signs of recent AI synthesis',
        'Content appears on unverified social media accounts only',
        'Claims contradict official statements from the actual person',
      ],
      health: [
        'Facial recognition mismatch with verified images of political figure',
        'Speech patterns inconsistent with known public addresses',
        'Video background contains digital artifacts from AI generation',
        'Content promotes agenda contrary to official policy positions',
        'Posted by newly created account with fake verification badges',
      ],
      news: [
        'Source not found in verified news organization databases',
        'Image manipulation detected in 3 out of 5 photos analyzed',
        'Claims directly contradict multiple credible news sources',
        'Website domain mimics legitimate news outlet with slight variations',
        'No verifiable author credentials or editorial board information',
      ],
      general: [
        'AI-generated content patterns detected across multiple indicators',
        'Facial analysis reveals manipulation and synthesis indicators',
        'Account created recently with suspicious engagement patterns',
        'Content shows characteristics of coordinated inauthentic behavior',
        'Multiple red flags identified in comprehensive credibility assessment',
      ],
    };
    return findings[type];
  };

  const getContextualActions = (type: ContentType, score: number): AnalysisResult['whatToDo'] => {
    const actions: { [key in ContentType]: AnalysisResult['whatToDo'] } = {
      investment: {
        dontDo: [
          'Do NOT transfer any money or provide banking/credit card details',
          'Do NOT share personal identification documents or passwords',
          'Do NOT click on investment links or download any files from this source',
        ],
        shouldDo: [
          'Verify the celebrity endorsement through their official verified accounts',
          'Check if the investment firm is registered with SEC or financial authorities',
          'Report to your local financial fraud department immediately',
          'Consult with a licensed, independent financial advisor before investing',
        ],
        verifyThrough: [
          'SEC.gov (U.S. Securities and Exchange Commission)',
          'Celebrity\'s official verified social media accounts',
          'Better Business Bureau (BBB) or equivalent in your country',
        ],
      },
      job: {
        dontDo: [
          'Do NOT assume this is the real celebrity/CEO speaking',
          'Do NOT share or forward the video without warning others it may be fake',
          'Do NOT make decisions based solely on this video content',
        ],
        shouldDo: [
          'Check the person\'s official verified social media accounts for the same message',
          'Look for official press releases on company/celebrity websites',
          'Report the fake video to the platform and relevant authorities',
          'Alert friends/family who may have seen and believed the video',
        ],
        verifyThrough: [
          'Official company website press releases',
          'Celebrity\'s verified Twitter/Instagram/Facebook accounts',
          'Reputable news organizations reporting the same story',
        ],
      },
      health: {
        dontDo: [
          'Do NOT assume this represents the political figure\'s actual position',
          'Do NOT share the video as if it were authentic',
          'Do NOT let this video influence voting or political decisions',
        ],
        shouldDo: [
          'Check official government websites for authentic statements',
          'Look for fact-checking from reputable news organizations',
          'Report the deepfake to electoral authorities if during an election period',
          'Compare with verified videos from official government channels',
        ],
        verifyThrough: [
          'Official government websites and press offices',
          'Verified political party social media accounts',
          'FactCheck.org, PolitiFact, or equivalent fact-checkers',
        ],
      },
      news: {
        dontDo: [
          'Do NOT share the content without fact-checking multiple sources',
          'Do NOT make important decisions based solely on this source',
          'Do NOT engage with or amplify suspicious or unverified content',
        ],
        shouldDo: [
          'Cross-reference the story with established, trusted news outlets',
          'Check major fact-checking websites for debunking information',
          'Look for the story on AP News, Reuters, BBC, or similar sources',
          'Report misinformation to the social media platform hosting it',
        ],
        verifyThrough: [
          'AP News, Reuters, BBC News, or other wire services',
          'FactCheck.org, Snopes.com, or regional fact-checkers',
          'Original source documents if the article cites any',
        ],
      },
      general: {
        dontDo: [
          'Do NOT share personal, financial, or sensitive information',
          'Do NOT click on suspicious links or download unknown files',
          'Do NOT forward or share the content without proper verification',
        ],
        shouldDo: [
          'Verify information through official channels and trusted sources',
          'Check multiple established sources for similar information',
          'Report clearly fraudulent content to the platform administrators',
          'Use reverse image/video search tools to check authenticity',
        ],
        verifyThrough: [
          'Official websites and verified social media accounts',
          'Established, reputable news sources',
          'Recognized fact-checking websites and organizations',
        ],
      },
    };
    return actions[type];
  };

  const removeResult = (id: string) => {
    setResults(prev => prev.filter(r => r.id !== id));
    if (selectedResult === id) {
      setSelectedResult(results[0]?.id || null);
    }
  };

  const getRiskColor = (riskLevel: 'low' | 'medium' | 'high') => {
    switch (riskLevel) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
    }
  };

  const getRiskBg = (riskLevel: 'low' | 'medium' | 'high') => {
    switch (riskLevel) {
      case 'low': return 'bg-gradient-to-br from-green-50 to-green-100 border-green-300';
      case 'medium': return 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-300';
      case 'high': return 'bg-gradient-to-br from-red-50 to-red-100 border-red-300';
    }
  };

  const getTrustColor = (trustScore: number) => {
    if (trustScore > 70) return 'text-green-600';
    if (trustScore > 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrustBg = (trustScore: number) => {
    if (trustScore > 70) return 'bg-gradient-to-br from-green-50 to-green-100 border-green-300';
    if (trustScore > 40) return 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-300';
    return 'bg-gradient-to-br from-red-50 to-red-100 border-red-300';
  };

  const getMetricColor = (value: number) => {
    if (value > 70) return 'text-red-600 bg-red-100';
    if (value > 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getProgressColor = (value: number) => {
    if (value > 70) return 'bg-red-500';
    if (value > 40) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getRiskImpactColor = (level: 'low' | 'medium' | 'high') => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-700 border-green-300';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'high': return 'bg-red-100 text-red-700 border-red-300';
    }
  };

  const getThreatIcon = (iconName: string) => {
    switch (iconName) {
      case 'users': return <Users className="w-5 h-5" />;
      case 'sparkles': return <Sparkles className="w-5 h-5" />;
      case 'dollar': return <DollarSign className="w-5 h-5" />;
      case 'video': return <Video className="w-5 h-5" />;
      case 'zap': return <Zap className="w-5 h-5" />;
      case 'heart': return <Heart className="w-5 h-5" />;
      case 'mail': return <Mail className="w-5 h-5" />;
      case 'lock': return <Lock className="w-5 h-5" />;
      default: return <AlertTriangle className="w-5 h-5" />;
    }
  };

  const currentResult = results.find(r => r.id === selectedResult);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10 pt-8 animate-in fade-in slide-in-from-top duration-700">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 rounded-3xl shadow-2xl border border-blue-500/30 hover:scale-105 transition-transform duration-300">
              <img src={logo} alt="Frauda AI Logo" className="w-24 h-24 object-contain" />
            </div>
          </div>

          <div className="flex items-center justify-center mb-4">
            <div className="text-center">
              <h1 className="text-4xl text-white">Frauda AI Trust Intelligence</h1>
              <p className="text-blue-400 text-xl mt-1">Decision Support System for Social Media Safety</p>
            </div>
          </div>
          <p className="text-gray-300 mt-4 max-w-3xl mx-auto">
            Specialized detection for digital fraud scams, misinformation campaigns, and identity abuse targeting public figures
          </p>
        </div>

        {/* Input Section with Content Type Selector */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-8 border border-white/20 animate-in fade-in slide-in-from-bottom duration-700 delay-150">
          <div className="flex items-center justify-between mb-6">
            <label className="text-white text-lg">What type of content is this?</label>
            <div className="flex gap-2">
              <button
                onClick={() => setShowUploader(!showUploader)}
                className={`px-4 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 ${
                  showUploader
                    ? 'bg-purple-500 text-white hover:bg-purple-600'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                <Upload className="w-4 h-4" />
                Upload Files
              </button>
              <button
                onClick={() => {
                  setComparisonMode(!comparisonMode);
                  if (!comparisonMode) {
                    setResults([]);
                    setSelectedResult(null);
                  }
                }}
                className={`px-4 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 ${
                  comparisonMode
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                <Plus className="w-4 h-4" />
                Compare Mode
              </button>
            </div>
          </div>

          {/* Content Type Selector */}
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

          {/* File Uploader */}
          {showUploader && (
            <div className="mb-6 animate-in fade-in slide-in-from-top duration-300">
              <FileUploader
                onFileSelect={handleFileSelect}
                onUrlSubmit={handleUrlFromUploader}
              />
            </div>
          )}

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
              disabled={!link.trim() || isAnalyzing}
              className="px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 duration-200"
            >
              {isAnalyzing ? (
                <span className="flex items-center gap-2">
                  <Eye className="w-5 h-5 animate-pulse" />
                  Analyzing...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Analyze Risk
                  <ArrowRight className="w-5 h-5" />
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Comparison View */}
        {comparisonMode && results.length > 0 && (
          <div className="mb-8 animate-in fade-in slide-in-from-top duration-500">
            <h3 className="text-white mb-4">Analyzed Links ({results.length})</h3>
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
                    onClick={(e) => {
                      e.stopPropagation();
                      removeResult(result.id);
                    }}
                    className="absolute top-2 right-2 p-1 bg-red-500/80 hover:bg-red-600 rounded-full transition-all hover:scale-110 cursor-pointer"
                  >
                    <X className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`text-3xl ${getTrustColor(result.trustScore)}`}>
                      {result.trustScore}
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Trust Score</p>
                      <span className={`px-2 py-1 rounded-full text-xs uppercase ${getRiskImpactColor(result.riskLevel)}`}>
                        {result.riskLevel}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-300 text-sm truncate">{result.url}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results Dashboard */}
        {currentResult && (
          <div className="space-y-6">
            {/* Trust Score Card - NEW POSITIONING */}
            <div className={`rounded-2xl shadow-2xl p-8 border-2 ${getTrustBg(currentResult.trustScore)} animate-in fade-in zoom-in duration-500`}>
              <div className="grid md:grid-cols-3 gap-6 items-center">
                <div className="md:col-span-2">
                  <div className="flex items-center gap-3 mb-4">
                    <h2 className="text-gray-800 text-2xl">Content Trust Score</h2>
                    <span className={`px-4 py-1 rounded-full text-sm uppercase tracking-wide ${getRiskColor(currentResult.riskLevel)} bg-white animate-in fade-in slide-in-from-right duration-500 delay-200`}>
                      {currentResult.riskLevel === 'high' ? 'Low Trust' : currentResult.riskLevel === 'medium' ? 'Medium Trust' : 'High Trust'}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-4">
                    <div className={`text-7xl ${getTrustColor(currentResult.trustScore)} animate-in zoom-in duration-700 delay-300`}>
                      {currentResult.trustScore}
                      <span className="text-3xl">/100</span>
                    </div>
                    <div className="text-gray-700 animate-in fade-in slide-in-from-bottom duration-500 delay-400">
                      <p className="text-lg font-semibold">
                        {currentResult.trustScore > 70 ? 'Trustworthy Content' :
                         currentResult.trustScore > 40 ? 'Proceed with Caution' :
                         'High Risk - Do Not Trust'}
                      </p>
                      <p className="text-sm text-gray-600">Based on AI intelligence analysis</p>
                    </div>
                  </div>
                </div>
                <div className="flex justify-center animate-in zoom-in duration-500 delay-500">
                  <div className={`p-6 rounded-full transition-all duration-300 hover:scale-110 ${
                    currentResult.trustScore > 70 ? 'bg-green-200' :
                    currentResult.trustScore > 40 ? 'bg-yellow-200' :
                    'bg-red-200'
                  }`}>
                    {currentResult.trustScore > 70 ? <BadgeCheck className="w-20 h-20 text-green-600" /> :
                     currentResult.trustScore > 40 ? <AlertTriangle className="w-20 h-20 text-yellow-600" /> :
                     <Ban className="w-20 h-20 text-red-600" />}
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Impact Layer - NEW FEATURE */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-in fade-in slide-in-from-left duration-500">
              <h2 className="mb-6 flex items-center gap-2 text-white text-2xl">
                <TrendingUp className="w-7 h-7 text-orange-400" />
                Potential Risk Impact
              </h2>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-white/5 rounded-xl p-6 border border-white/10 hover:scale-105 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-6 h-6 text-red-400" />
                      <h3 className="text-white">Financial Risk</h3>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm uppercase font-semibold ${getRiskImpactColor(currentResult.riskImpact.financial)} border-2`}>
                      {currentResult.riskImpact.financial}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm">
                    {currentResult.riskImpact.financial === 'high'
                      ? 'Potential for significant financial loss'
                      : currentResult.riskImpact.financial === 'medium'
                      ? 'Moderate financial risk present'
                      : 'Low financial impact'}
                  </p>
                </div>

                <div className="bg-white/5 rounded-xl p-6 border border-white/10 hover:scale-105 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Users className="w-6 h-6 text-yellow-400" />
                      <h3 className="text-white">Reputation Risk</h3>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm uppercase font-semibold ${getRiskImpactColor(currentResult.riskImpact.reputation)} border-2`}>
                      {currentResult.riskImpact.reputation}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm">
                    {currentResult.riskImpact.reputation === 'high'
                      ? 'Sharing could damage your credibility'
                      : currentResult.riskImpact.reputation === 'medium'
                      ? 'Exercise caution before sharing'
                      : 'Low reputation impact'}
                  </p>
                </div>

                <div className="bg-white/5 rounded-xl p-6 border border-white/10 hover:scale-105 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-6 h-6 text-purple-400" />
                      <h3 className="text-white">Misinformation Risk</h3>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm uppercase font-semibold ${getRiskImpactColor(currentResult.riskImpact.misinformation)} border-2`}>
                      {currentResult.riskImpact.misinformation}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm">
                    {currentResult.riskImpact.misinformation === 'high'
                      ? 'Contains false or misleading information'
                      : currentResult.riskImpact.misinformation === 'medium'
                      ? 'Some claims require verification'
                      : 'Low misinformation risk'}
                  </p>
                </div>
              </div>
            </div>

            {/* What Should I Do? - DECISION ENGINE */}
            <div className="bg-gradient-to-r from-red-600 via-orange-600 to-red-600 rounded-2xl shadow-2xl p-8 text-white animate-in fade-in zoom-in duration-500">
              <h2 className="mb-6 flex items-center gap-3 text-2xl">
                <Shield className="w-8 h-8" />
                What Should I Do?
              </h2>

              <div className="grid md:grid-cols-3 gap-6">
                {/* DON'T DO */}
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <XCircle className="w-6 h-6" />
                    <h3 className="text-lg font-semibold">DON'T</h3>
                  </div>
                  <ul className="space-y-2">
                    {currentResult.whatToDo.dontDo.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <Ban className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* SHOULD DO */}
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="w-6 h-6" />
                    <h3 className="text-lg font-semibold">DO</h3>
                  </div>
                  <ul className="space-y-2">
                    {currentResult.whatToDo.shouldDo.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <ArrowRight className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* VERIFY THROUGH */}
                <div className="bg-white/10 backdrop-blur rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <BadgeCheck className="w-6 h-6" />
                    <h3 className="text-lg font-semibold">Verify Through</h3>
                  </div>
                  <ul className="space-y-2">
                    {currentResult.whatToDo.verifyThrough.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Explainable Findings - Human Language */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-in fade-in slide-in-from-bottom duration-500">
              <h2 className="mb-6 flex items-center gap-2 text-white text-2xl">
                <Eye className="w-7 h-7 text-blue-400" />
                Why This Looks Suspicious
              </h2>
              <p className="text-gray-300 mb-4">Here's what our AI detected in plain language:</p>
              <ul className="space-y-3">
                {currentResult.explainableFindings.map((item, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-3 p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 hover:border-blue-400/30 hover:translate-x-2 transition-all duration-300 animate-in fade-in slide-in-from-left"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <span className="w-7 h-7 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-sm font-semibold hover:scale-110 transition-transform">
                      {index + 1}
                    </span>
                    <span className="text-gray-200">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Detection Metrics - Technical Layer */}
            <details className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:bg-white/10 transition-all cursor-pointer">
              <summary className="text-white text-lg mb-4 cursor-pointer flex items-center gap-2">
                <TrendingDown className="w-6 h-6 text-gray-400" />
                Technical Detection Metrics (Advanced)
              </summary>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                {[
                  { key: 'aiGenerated', label: 'AI-Generated', icon: <Sparkles className="w-5 h-5" />, color: 'purple' },
                  { key: 'deepfake', label: 'Deepfake', icon: <Video className="w-5 h-5" />, color: 'pink' },
                  { key: 'impersonation', label: 'Impersonation', icon: <Users className="w-5 h-5" />, color: 'blue' },
                  { key: 'misinformation', label: 'Misinformation', icon: <DollarSign className="w-5 h-5" />, color: 'green' },
                  { key: 'phishing', label: 'Phishing', icon: <Mail className="w-5 h-5" />, color: 'orange' },
                  { key: 'identityTheft', label: 'Identity Theft', icon: <Lock className="w-5 h-5" />, color: 'indigo' },
                ].map((metric, index) => {
                  const value = currentResult.detectionMetrics[metric.key as keyof typeof currentResult.detectionMetrics];
                  if (value === 0) return null;
                  return (
                    <div
                      key={metric.key}
                      className="bg-white/5 rounded-xl p-4 border border-white/10 hover:scale-105 transition-all"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`text-${metric.color}-400`}>
                            {metric.icon}
                          </div>
                          <h3 className="text-white text-sm">{metric.label}</h3>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getMetricColor(value)}`}>
                          {value}%
                        </span>
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
                onClick={() => {
                  if (!comparisonMode) {
                    setResults([]);
                    setSelectedResult(null);
                  }
                  setLink('');
                  setUploadedFiles([]);
                }}
                className="px-6 py-3 bg-white/10 backdrop-blur border-2 border-white/30 text-white rounded-xl hover:bg-white/20 hover:scale-105 active:scale-95 transition-all duration-200"
              >
                Analyze Another Link
              </button>
              <button
                onClick={() => alert('Downloading detailed intelligence report...')}
                className="px-6 py-3 bg-white text-gray-900 rounded-xl hover:bg-gray-100 hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg"
              >
                Download Full Report
              </button>
              <button
                onClick={() => setIsReportModalOpen(true)}
                className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg"
              >
                Report to Authorities
              </button>
            </div>
          </div>
        )}

        {/* Report Modal */}
        {currentResult && (
          <ReportModal
            isOpen={isReportModalOpen}
            onClose={() => setIsReportModalOpen(false)}
            analysisData={{
              url: currentResult.url,
              contentType: currentResult.contentType,
              trustScore: currentResult.trustScore,
              riskLevel: currentResult.riskLevel,
              uploadedFiles: currentResult.uploadedFiles,
            }}
          />
        )}

        {/* Empty State */}
        {!currentResult && !isAnalyzing && (
          <div className="text-center py-16 animate-in fade-in zoom-in duration-700">
            <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-6 max-w-6xl mx-auto mb-12">
              {[
                { icon: <DollarSign className="w-12 h-12 mx-auto mb-3 text-green-400" />, title: 'Investment Scams', desc: 'Fake financial opportunities & crypto fraud', delay: 0 },
                { icon: <Video className="w-12 h-12 mx-auto mb-3 text-pink-400" />, title: 'Deepfake Videos', desc: 'AI-manipulated video content', delay: 100 },
                { icon: <Users className="w-12 h-12 mx-auto mb-3 text-blue-400" />, title: 'CEO Impersonation', desc: 'Fake executive endorsements', delay: 200 },
                { icon: <BadgeCheck className="w-12 h-12 mx-auto mb-3 text-purple-400" />, title: 'Political Deepfakes', desc: 'Fake Prime Minister/President videos', delay: 300 },
                { icon: <FileText className="w-12 h-12 mx-auto mb-3 text-indigo-400" />, title: 'Fake News', desc: 'Misinformation & false narratives', delay: 400 },
                { icon: <Sparkles className="w-12 h-12 mx-auto mb-3 text-yellow-400" />, title: 'Celebrity Scams', desc: 'Fraudulent celebrity endorsements', delay: 500 },
              ].map((card, index) => (
                <div
                  key={index}
                  className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 hover:scale-110 hover:shadow-2xl hover:border-white/40 transition-all duration-300 cursor-pointer animate-in fade-in zoom-in"
                  style={{ animationDelay: `${card.delay}ms` }}
                >
                  {card.icon}
                  <h3 className="text-white mb-2 font-semibold text-sm">{card.title}</h3>
                  <p className="text-gray-400 text-xs">{card.desc}</p>
                </div>
              ))}
            </div>
            <Shield className="w-24 h-24 mx-auto mb-4 text-blue-400/30 animate-pulse" />
            <p className="text-gray-300 text-lg mb-2">Select content type and paste a link to begin analysis</p>
            <p className="text-gray-400 text-sm max-w-2xl mx-auto">
              Specialized in detecting digital fraud, misinformation campaigns, and identity abuse of public figures
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
