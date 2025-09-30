import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  MessageCircle,
  TrendingUp,
  Clock,
  HelpCircle,
  Megaphone,
  Search,
  Filter,
  ThumbsUp,
  MessageSquare,
  AlertTriangle
} from 'lucide-react';

interface ForumPost {
  id: string;
  title: string;
  content: string;
  author: string;
  author_avatar: string;
  category: string;
  created_at: string;
  replies_count: number;
  likes_count: number;
  is_pinned: boolean;
  is_answered: boolean;
  tags: string[];
}

export default function CommunityForum() {
  const [posts, setPosts] = useState<ForumPost[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewPostModal, setShowNewPostModal] = useState(false);
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    category: 'general'
  });

  const categories = [
    { id: 'all', name: 'All Posts', icon: MessageCircle },
    { id: 'trending', name: 'Trending', icon: TrendingUp },
    { id: 'latest', name: 'Latest', icon: Clock },
    { id: 'questions', name: 'Q&A', icon: HelpCircle },
    { id: 'announcements', name: 'Announcements', icon: Megaphone }
  ];

  useEffect(() => {
    // Simulate loading forum posts
    setPosts([
      {
        id: '1',
        title: '🔥 How to implement OAuth 2.1 with PKCE in React?',
        content: 'I\'m trying to implement OAuth 2.1 with PKCE in my React application but running into some issues with the authorization flow...',
        author: 'dev_mike',
        author_avatar: 'https://via.placeholder.com/40',
        category: 'questions',
        created_at: '2 hours ago',
        replies_count: 23,
        likes_count: 45,
        is_pinned: false,
        is_answered: false,
        tags: ['oauth', 'react', 'pkce']
      },
      {
        id: '2',
        title: '🚨 URGENT: API Rate Limiting Changes - Action Required',
        content: 'Starting March 1st, we\'re implementing new rate limiting policies. All developers need to update their applications...',
        author: 'techcorp_admin',
        author_avatar: 'https://via.placeholder.com/40',
        category: 'announcements',
        created_at: '1 day ago',
        replies_count: 156,
        likes_count: 89,
        is_pinned: true,
        is_answered: true,
        tags: ['api', 'rate-limiting', 'announcement']
      },
      {
        id: '3',
        title: '🎉 New Python SDK v2.4.0 Released!',
        content: 'We\'re excited to announce the release of our Python SDK v2.4.0 with improved error handling and new OAuth features...',
        author: 'sdk_team',
        author_avatar: 'https://via.placeholder.com/40',
        category: 'announcements',
        created_at: '3 days ago',
        replies_count: 45,
        likes_count: 123,
        is_pinned: false,
        is_answered: true,
        tags: ['sdk', 'python', 'release']
      },
      {
        id: '4',
        title: 'JWT Token Validation Best Practices?',
        content: 'What are the current best practices for JWT token validation in 2024? I want to make sure I\'m implementing security correctly...',
        author: 'security_sarah',
        author_avatar: 'https://via.placeholder.com/40',
        category: 'questions',
        created_at: '5 days ago',
        replies_count: 34,
        likes_count: 67,
        is_pinned: false,
        is_answered: true,
        tags: ['jwt', 'security', 'validation']
      },
      {
        id: '5',
        title: 'GraphQL API Introspection - is it safe in production?',
        content: 'I noticed our GraphQL endpoint has introspection enabled. Should this be disabled in production environments?',
        author: 'backend_bob',
        author_avatar: 'https://via.placeholder.com/40',
        category: 'questions',
        created_at: '1 week ago',
        replies_count: 12,
        likes_count: 28,
        is_pinned: false,
        is_answered: false,
        tags: ['graphql', 'security', 'production']
      }
    ]);
  }, []);

  const handleNewPost = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // 🚨 VULNERABILITY: This will be vulnerable to XSS in Stage 2
      const response = await fetch('/api/community/posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newPost.title,
          content: newPost.content, // No XSS protection
          category: newPost.category
        })
      });

      const result = await response.json();

      if (response.ok) {
        // Add new post to list
        const newForumPost: ForumPost = {
          id: result.id,
          title: newPost.title,
          content: newPost.content,
          author: 'current_user',
          author_avatar: 'https://via.placeholder.com/40',
          category: newPost.category,
          created_at: 'Just now',
          replies_count: 0,
          likes_count: 0,
          is_pinned: false,
          is_answered: false,
          tags: []
        };

        setPosts([newForumPost, ...posts]);
        setShowNewPostModal(false);
        setNewPost({ title: '', content: '', category: 'general' });
      }
    } catch (error) {
      console.error('Failed to create post:', error);
    }
  };

  const filteredPosts = posts.filter(post => {
    if (selectedCategory !== 'all' && post.category !== selectedCategory) {
      return false;
    }
    if (searchQuery && !post.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <>
      <Head>
        <title>Developer Community - TechCorp Connect</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex items-center">
                  <MessageCircle className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">TechCorp Connect</span>
                </Link>
                <nav className="ml-10 flex space-x-8">
                  <Link href="/developer/dashboard" className="text-gray-500 hover:text-gray-700 px-1 pb-4 text-sm font-medium">
                    Dashboard
                  </Link>
                  <Link href="/developer/applications" className="text-gray-500 hover:text-gray-700 px-1 pb-4 text-sm font-medium">
                    Applications
                  </Link>
                  <Link href="/community" className="text-blue-600 border-b-2 border-blue-600 px-1 pb-4 text-sm font-medium">
                    Community
                  </Link>
                </nav>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm">
                  <span className="text-gray-500">Welcome back,</span>
                  <span className="font-medium text-gray-900 ml-1">John Developer</span>
                </div>
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">JD</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex gap-8">
            {/* Sidebar */}
            <div className="w-64 flex-shrink-0">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Categories</h2>
                <nav className="space-y-2">
                  {categories.map((category) => {
                    const Icon = category.icon;
                    return (
                      <button
                        key={category.id}
                        onClick={() => setSelectedCategory(category.id)}
                        className={`w-full flex items-center px-3 py-2 rounded-md text-sm ${
                          selectedCategory === category.id
                            ? 'bg-blue-100 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        <Icon className="h-4 w-4 mr-3" />
                        {category.name}
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Quick Stats */}
              <div className="bg-white rounded-lg shadow-sm border p-6 mt-6">
                <h3 className="font-semibold text-gray-900 mb-4">Community Stats</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Active Users</span>
                    <span className="font-medium">1,247</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Posts</span>
                    <span className="font-medium">8,932</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Answered</span>
                    <span className="font-medium text-green-600">94%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="flex-1">
              {/* Search and Actions */}
              <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
                <div className="flex justify-between items-center mb-4">
                  <h1 className="text-2xl font-bold text-gray-900">Developer Community</h1>
                  <button
                    onClick={() => setShowNewPostModal(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    New Post
                  </button>
                </div>

                <div className="flex gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search discussions..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <button className="flex items-center px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                  </button>
                </div>
              </div>

              {/* Posts List */}
              <div className="space-y-4">
                {filteredPosts.map((post) => (
                  <div key={post.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                    <div className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            {post.is_pinned && (
                              <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full mr-2">
                                Pinned
                              </span>
                            )}
                            {post.is_answered && (
                              <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mr-2">
                                ✓ Answered
                              </span>
                            )}
                            <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                              {post.category}
                            </span>
                          </div>

                          <h3 className="text-lg font-semibold text-gray-900 mb-2 hover:text-blue-600 cursor-pointer">
                            <Link href={`/community/post/${post.id}`}>
                              {post.title}
                            </Link>
                          </h3>

                          <p className="text-gray-600 mb-3 line-clamp-2">
                            {post.content}
                          </p>

                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <div className="flex items-center">
                                <img
                                  src={post.author_avatar}
                                  alt={post.author}
                                  className="w-6 h-6 rounded-full mr-2"
                                />
                                <span className="text-sm text-gray-700 font-medium">@{post.author}</span>
                                <span className="text-sm text-gray-500 ml-2">{post.created_at}</span>
                              </div>
                            </div>

                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <div className="flex items-center">
                                <ThumbsUp className="h-4 w-4 mr-1" />
                                {post.likes_count}
                              </div>
                              <div className="flex items-center">
                                <MessageSquare className="h-4 w-4 mr-1" />
                                {post.replies_count}
                              </div>
                            </div>
                          </div>

                          {post.tags.length > 0 && (
                            <div className="flex gap-2 mt-3">
                              {post.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-md"
                                >
                                  #{tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* New Post Modal */}
        {showNewPostModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-[700px] shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Post</h3>

                <form onSubmit={handleNewPost} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Title
                    </label>
                    <input
                      type="text"
                      required
                      value={newPost.title}
                      onChange={(e) => setNewPost({...newPost, title: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="What's your question or discussion topic?"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={newPost.category}
                      onChange={(e) => setNewPost({...newPost, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="general">General Discussion</option>
                      <option value="questions">Questions & Help</option>
                      <option value="showcase">Show & Tell</option>
                      <option value="feedback">Feedback</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Content
                    </label>
                    <textarea
                      required
                      rows={8}
                      value={newPost.content}
                      onChange={(e) => setNewPost({...newPost, content: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Share your thoughts, ask your question, or start a discussion... (HTML supported for formatting)"
                    />
                    <div className="mt-2 text-xs text-gray-500">
                      <AlertTriangle className="inline h-3 w-3 mr-1" />
                      Note: HTML is allowed for rich formatting, but be careful with user-generated content!
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowNewPostModal(false)}
                      className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Create Post
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}