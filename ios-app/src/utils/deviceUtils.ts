import { Platform } from 'react-native';
import DeviceInfo from 'react-native-device-info';

export async function generateClientId(): Promise<string> {
  try {
    const deviceId = await DeviceInfo.getUniqueId();
    const platform = Platform.OS;
    const timestamp = Date.now();
    
    return `${platform}_${deviceId}_${timestamp}`;
  } catch (error) {
    // Fallback if DeviceInfo is not available
    const platform = Platform.OS;
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    
    return `${platform}_${timestamp}_${random}`;
  }
}

export function getPlatformInfo() {
  return {
    platform: Platform.OS,
    version: Platform.Version,
    isIOS: Platform.OS === 'ios',
    isAndroid: Platform.OS === 'android',
  };
}