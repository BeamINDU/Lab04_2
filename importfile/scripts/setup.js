const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

async function main() {
  console.log('🚀 Starting database setup...');

  // Create companies
  const companies = [
    {
      id: 'company-a-id',
      name: 'SiamTech Main Office',
      code: 'company_a',
      dbName: 'siamtech_company_a',
      description: 'สำนักงานใหญ่ สยามเทค จำกัด',
      location: 'กรุงเทพมหานคร'
    },
    {
      id: 'company-b-id', 
      name: 'SiamTech Regional Office',
      code: 'company_b',
      dbName: 'siamtech_company_b',
      description: 'สาขาภาคเหนือ สยามเทค จำกัด',
      location: 'เชียงใหม่'
    },
    {
      id: 'company-c-id',
      name: 'SiamTech International',
      code: 'company_c', 
      dbName: 'siamtech_company_c',
      description: 'สำนักงานต่างประเทศ สยามเทค จำกัด',
      location: 'International'
    }
  ];

  console.log('📊 Creating companies...');
  for (const company of companies) {
    await prisma.company.upsert({
      where: { code: company.code },
      update: company,
      create: company,
    });
    console.log(`✅ Company created: ${company.name}`);
  }

  // Create admin users for each company
  const hashedPassword = await bcrypt.hash('password123', 12);
  
  const users = [
    {
      email: 'admin.a@siamtech.com',
      name: 'Admin Company A',
      password: hashedPassword,
      companyId: 'company-a-id',
      role: 'ADMIN'
    },
    {
      email: 'admin.b@siamtech.com', 
      name: 'Admin Company B',
      password: hashedPassword,
      companyId: 'company-b-id',
      role: 'ADMIN'
    },
    {
      email: 'admin.c@siamtech.com',
      name: 'Admin Company C', 
      password: hashedPassword,
      companyId: 'company-c-id',
      role: 'ADMIN'
    },
    // Regular users
    {
      email: 'manager.a@siamtech.com',
      name: 'Manager Company A',
      password: hashedPassword,
      companyId: 'company-a-id',
      role: 'MANAGER'
    },
    {
      email: 'user.a@siamtech.com',
      name: 'User Company A',
      password: hashedPassword,
      companyId: 'company-a-id',
      role: 'USER'
    }
  ];

  console.log('👥 Creating users...');
  for (const user of users) {
    await prisma.user.upsert({
      where: { email: user.email },
      update: user,
      create: user,
    });
    console.log(`✅ User created: ${user.email}`);
  }

  console.log('✨ Database setup completed!');
  console.log('\n🔑 Demo Login Credentials:');
  console.log('Company A Admin: admin.a@siamtech.com / password123');
  console.log('Company B Admin: admin.b@siamtech.com / password123'); 
  console.log('Company C Admin: admin.c@siamtech.com / password123');
  console.log('Company A Manager: manager.a@siamtech.com / password123');
  console.log('Company A User: user.a@siamtech.com / password123');
}

main()
  .catch((e) => {
    console.error('❌ Setup failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
