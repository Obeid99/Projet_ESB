'use client';
import { Box, Text, useColorModeValue } from '@chakra-ui/react';

export default function FooterAdmin() {
  const textColor = useColorModeValue('gray.600', 'gray.400');

  return (
    <Box as="footer" py="4" textAlign="center" bg="transparent">
      <Text fontSize="sm" color={textColor}>
        © {new Date().getFullYear()} ESPRIT SCHOOL OF BUSINESS. All rights reserved.
      </Text>
    </Box>
  );
}
