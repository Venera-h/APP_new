export interface PracticalWorkBase {
  work_name: string;
  student: string;
  variant_number: number;
  level_number: number;
  submission_date: string;
  grade: number;
}

export interface PracticalWorkCreate extends PracticalWorkBase {
  title: string;
  content: string;
}

export interface PracticalWorkOut extends PracticalWorkBase {
  id: number;
  title: string;
  content: string;
  owner_id: number;
}

export interface PracticalWorkUpdate {
  work_name?: string;
  student?: string;
  variant_number?: number;
  level_number?: number;
  submission_date?: string;
  grade?: number;
  title?: string;
  content?: string;
}

export interface User {
  login: string;
  password: string;
}

export interface TokenResponse {
  token: string;
}