export interface ABTest {
  name: string;
  description?: string;
  platform: 'web' | 'ios' | 'both';
  trafficAllocation: number; // 0.0 to 1.0
  startDate?: Date;
  endDate?: Date;
  variants: ABTestVariant[];
}

export interface ABTestVariant {
  name: string;
  description?: string;
  trafficWeight: number; // 0.0 to 1.0
  config: any;
  isControl: boolean;
}

export interface ABTestAssignment {
  testId: string;
  variantId: string;
  variantName: string;
  config: any;
  assignedAt: Date;
}