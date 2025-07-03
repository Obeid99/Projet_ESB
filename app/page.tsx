'use client';

import { Box, Button, Flex, Text, VStack } from '@chakra-ui/react';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/welcome'); 
  }, [router]);

  return null; 
}
