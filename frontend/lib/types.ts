// API Response Types

export type ConversationMessage = {
  speaker: 'user' | 'hera' | 'partner' | 'child' | 'family' | string;
  message: string;
  timestamp?: string;
};

export type InformationProgress = {
  basic_info?: {
    collected: number;
    total: number;
  };
  relationship?: {
    collected: number;
    total: number;
  };
  lifestyle?: {
    collected: number;
    total: number;
  };
  personality?: {
    collected: number;
    total: number;
  };
  children_info?: {
    collected: number;
    total: number;
  };
};

export type UserProfile = {
  name?: string;
  age?: number;
  gender?: string;
  relationship_status?: string;
  income?: string;
  lifestyle?: Record<string, any>;
  user_personality_traits?: Record<string, any>;
  partner_face_description?: string;
  children_info?: Array<Record<string, any>>;
  [key: string]: any;
};

export type SessionResponse = {
  session_id: string;
  created_at: string;
  status: string;
};

export type MessageResponse = {
  reply: string | ConversationMessage[];
  conversation_history: ConversationMessage[];
  user_profile: UserProfile;
  information_progress: InformationProgress;
  missing_fields: string[];
  profile_complete: boolean;
  session_status?: string;
  completion_message?: string | null;
  last_extracted_fields?: Record<string, any>;
};

export type StatusResponse = {
  user_profile: UserProfile;
  conversation_history: ConversationMessage[];
  information_progress: InformationProgress;
  missing_fields: string[];
  profile_complete: boolean;
};

export type CompleteResponse = {
  message: string;
  user_profile: UserProfile;
  conversation_history: ConversationMessage[];
  information_progress: InformationProgress;
  missing_fields: string[];
  information_complete: boolean;
  error?: string;
};

export type FamilyMessage = {
  speaker: string;
  message: string;
  timestamp?: string;
};

export type FamilyStatusResponse = {
  conversation_history: ConversationMessage[];
  family_trip_info: Record<string, any>;
  conversation_complete: boolean;
  error?: string;
};

export type FamilyMessageResponse = {
  reply: FamilyMessage[];
  conversation_history: ConversationMessage[];
  family_trip_info: Record<string, any>;
  conversation_complete: boolean;
  error?: string;
};
